"""LAPTOP field calibration of the yellow-boundary HSV thresholds.

Subscribes to the Pinky camera over ROS 2 (never opens a camera device, never
publishes anything, so it cannot move the robot). Click the yellow boundary
>= 5 times, check the live mask, ENTER saves the six yellow_* keys.
Run via scripts/ksam_hsv_calibrate.
"""

import argparse
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage

from pinky_camera_drive import hsv_deploy, hsv_utils

WINDOW = 'ksam_hsv_calibrate'
PANEL_HEIGHT = 150
DEFAULT_CONFIG = (
    Path(__file__).resolve().parents[1] / 'config' / 'camera_straight_drive.yaml')


class FrameSource:
    """Keep only the latest decoded camera frame."""

    def __init__(self, node, topic):
        self.frame = None
        self.stamp = None
        node.create_subscription(
            CompressedImage, topic, self._callback, qos_profile_sensor_data)

    def _callback(self, msg):
        frame = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
        if frame is not None:
            self.frame = frame
            self.stamp = time.monotonic()

    def age(self):
        return float('inf') if self.stamp is None else time.monotonic() - self.stamp


def bounds_text(lower, upper):
    return (f'H {lower[0]}-{upper[0]}  S {lower[1]}-{upper[1]}  '
            f'V {lower[2]}-{upper[2]}')


def yaml_bounds(params):
    lower = np.array([params[k] for k in hsv_utils.HSV_KEYS[0::2]], np.uint8)
    upper = np.array([params[k] for k in hsv_utils.HSV_KEYS[1::2]], np.uint8)
    return lower, upper


class Calibrator:
    def __init__(self, args, params):
        self.args = args
        self.yaml_lower, self.yaml_upper = yaml_bounds(params)
        self.roi = (
            float(params.get('roi_top_ratio', 0.65)),
            float(params.get('roi_left_ratio', 0.0)),
            float(params.get('roi_right_ratio', 0.70)),
        )
        self.reset()

    def reset(self):
        self.clicks = []  # (x, y, pixels, ok, reason)
        self.pending = []
        self.confirm_warnings = False
        self.message = 'click the yellow boundary'

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pending.append((x, y))

    def take_pending_clicks(self, hsv):
        height, width = hsv.shape[:2]
        for x, y in self.pending:
            if not (0 <= x < width and 0 <= y < height):
                continue  # click on the text panel
            pixels = hsv_utils.sample_patch(hsv, x, y, self.args.patch)
            ok, reason = hsv_utils.is_plausible_yellow(pixels)
            self.clicks.append((x, y, pixels, ok, reason))
            self.confirm_warnings = False
            self.message = (f'click {len(self.clicks)} accepted' if ok else
                            f'click {len(self.clicks)} REJECTED: {reason}')
            print(f'[hsv] {self.message} at ({x}, {y})')
        self.pending.clear()

    def valid_pixels(self):
        good = [c[2] for c in self.clicks if c[3]]
        return len(good), (np.concatenate(good) if good else np.empty((0, 3)))

    def proposal(self, hsv):
        """Return (lower, upper, diagnostics, warnings, error)."""
        count, pixels = self.valid_pixels()
        if count < self.args.min_clicks:
            return None, None, {}, [], (
                f'need {self.args.min_clicks} valid clicks (have {count})')
        try:
            lower, upper = hsv_utils.robust_hsv_bounds(pixels)
        except ValueError as exc:
            return None, None, {}, [], f'cannot compute range: {exc}'
        roi = self.roi_view(hsv)
        diag = {
            'sample': hsv_utils.in_range_fraction(pixels, lower, upper),
            'roi': float(np.mean(cv2.inRange(roi, lower, upper) > 0)),
        }
        warnings = []
        if diag['sample'] < self.args.min_sample_coverage:
            warnings.append(
                f"only {diag['sample']:.0%} of clicked pixels detected")
        if diag['roi'] > self.args.max_roi_coverage:
            warnings.append(
                f"mask covers {diag['roi']:.0%} of drive ROI (too broad?)")
        return lower, upper, diag, warnings, None

    def roi_box(self, shape):
        height, width = shape[:2]
        top, left, right = self.roi
        return int(width * left), int(height * top), int(width * right), height

    def roi_view(self, image):
        x0, y0, x1, y1 = self.roi_box(image.shape)
        return image[y0:y1, x0:x1]

    def render(self, frame, hsv, proposal, stale):
        lower, upper, diag, warnings, error = proposal
        preview_lower, preview_upper = (
            (lower, upper) if lower is not None
            else (self.yaml_lower, self.yaml_upper))
        mask = cv2.inRange(hsv, preview_lower, preview_upper) > 0
        view = frame.copy()
        view[mask] = (0.35 * view[mask] + 0.65 * np.array([255, 0, 255])).astype(
            np.uint8)
        x0, y0, x1, y1 = self.roi_box(frame.shape)
        cv2.rectangle(view, (x0, y0), (x1 - 1, y1 - 1), (255, 255, 0), 1)
        half = self.args.patch // 2
        for index, (x, y, _, ok, _) in enumerate(self.clicks, 1):
            color = (0, 255, 0) if ok else (0, 0, 255)
            cv2.rectangle(view, (x - half, y - half), (x + half, y + half),
                          color, 1)
            if not ok:
                cv2.line(view, (x - half, y - half), (x + half, y + half),
                         color, 2)
                cv2.line(view, (x - half, y + half), (x + half, y - half),
                         color, 2)
            cv2.putText(view, str(index), (x + half + 2, y - half),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        count, _ = self.valid_pixels()
        rejected = len(self.clicks) - count
        lines = [
            (f'valid clicks {count} (rejected {rejected}), '
             f'patch {self.args.patch}x{self.args.patch}', (255, 255, 255)),
        ]
        if lower is not None:
            lines.append(('PROPOSED  ' + bounds_text(lower, upper),
                          (0, 255, 0)))
            lines.append((f"sample coverage {diag['sample']:.0%}   "
                          f"drive-ROI coverage {diag['roi']:.0%}",
                          (255, 255, 255)))
        else:
            lines.append(('preview = CURRENT YAML  '
                          + bounds_text(self.yaml_lower, self.yaml_upper),
                          (0, 200, 255)))
            lines.append((error, (0, 200, 255)))
        for warning in warnings:
            lines.append(('WARNING: ' + warning, (0, 0, 255)))
        if stale:
            lines.append((f'CAMERA STALE ({stale:.1f}s) - saving disabled',
                          (0, 0, 255)))
        lines.append((self.message, (200, 200, 200)))
        lines.append(('ENTER=APPLY/SAVE   R=RESET clicks   ESC/Q=CANCEL',
                      (255, 255, 0)))

        panel = np.zeros(
            (max(PANEL_HEIGHT, 18 * len(lines) + 8), view.shape[1], 3), np.uint8)
        for row, (text, color) in enumerate(lines):
            cv2.putText(panel, text, (6, 18 + 18 * row),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
        return np.vstack([view, panel])

    def try_save(self, proposal, stale):
        lower, upper, diag, warnings, error = proposal
        if stale:
            self.message = 'camera stale: not saving'
            return False
        if error:
            self.message = f'not saving: {error}'
            return False
        try:
            hsv_utils.validate_bounds(lower, upper)
        except ValueError as exc:
            self.message = f'not saving: {exc}'
            return False
        if warnings and not self.confirm_warnings:
            self.confirm_warnings = True
            self.message = 'WARNINGS above: press ENTER again to save anyway, R to redo'
            print('[hsv] ' + '; '.join(warnings))
            return False

        new = dict(zip(hsv_utils.HSV_KEYS[0::2], (int(v) for v in lower)))
        new.update(zip(hsv_utils.HSV_KEYS[1::2], (int(v) for v in upper)))
        try:
            old, backup = hsv_utils.update_hsv_yaml(self.args.config, new)
        except Exception as exc:  # noqa: BLE001 - report, keep window open
            self.message = f'SAVE FAILED (YAML untouched): {exc}'
            print('[hsv] ' + self.message, file=sys.stderr)
            return False
        print('[hsv] SAVED')
        for key in hsv_utils.HSV_KEYS:
            print(f'  {key}: {old[key]} -> {new[key]}')
        print(f"  sample coverage {diag['sample']:.0%}, "
              f"drive-ROI coverage {diag['roi']:.0%}")
        print(f'  config: {self.args.config}')
        print(f'  backup: {backup}')
        return True


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--config', default=str(DEFAULT_CONFIG))
    parser.add_argument('--topic', default='/camera/image/compressed')
    parser.add_argument('--patch', type=int, default=11,
                        help='sample patch size in pixels (odd, default 11)')
    parser.add_argument('--min-clicks', type=int, default=5)
    parser.add_argument('--wait', type=float, default=10.0,
                        help='seconds to wait for the first camera frame')
    parser.add_argument('--stale-exit', type=float, default=5.0,
                        help='exit if no frame arrives for this many seconds')
    parser.add_argument('--min-sample-coverage', type=float, default=0.80)
    parser.add_argument('--max-roi-coverage', type=float, default=0.40)
    parser.add_argument('--no-deploy', action='store_true',
                        help='save the laptop YAML only; do not copy to Pinky')
    args = parser.parse_args(argv)
    args.patch = max(3, args.patch | 1)
    args.min_clicks = max(5, args.min_clicks)
    return args


def run(args):
    params = hsv_utils.read_ros_params(args.config)
    calibrator = Calibrator(args, params)
    print(f'[hsv] config: {args.config}')
    print('[hsv] current YAML: '
          + bounds_text(calibrator.yaml_lower, calibrator.yaml_upper))
    print(f"[hsv] ROS_DOMAIN_ID={os.environ.get('ROS_DOMAIN_ID', '0 (unset)')}")
    print(f'[hsv] waiting for {args.topic} ...')

    rclpy.init()
    node = rclpy.create_node('ksam_hsv_calibrate')
    source = FrameSource(node, args.topic)
    try:
        deadline = time.monotonic() + args.wait
        while source.frame is None and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if source.frame is None:
            print(f'[hsv] ERROR: no frame on {args.topic} within {args.wait:.0f}s.'
                  ' Is the Pinky camera running and ROS_DOMAIN_ID the same? '
                  'YAML untouched.', file=sys.stderr)
            return 2
        height, width = source.frame.shape[:2]
        print(f'[hsv] camera stream connected ({width}x{height})')
        print(f'[hsv] click the yellow boundary at least {args.min_clicks} times')
        print('[hsv] ENTER=save  R=reset  ESC/Q=cancel')

        cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WINDOW, calibrator.on_mouse)
        while True:
            rclpy.spin_once(node, timeout_sec=0.0)
            age = source.age()
            if age > args.stale_exit:
                print(f'[hsv] ERROR: camera stream stale for {age:.1f}s; '
                      'exiting, YAML untouched.', file=sys.stderr)
                return 3
            stale = age if age > 1.0 else 0.0
            frame = source.frame
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            calibrator.take_pending_clicks(hsv)
            proposal = calibrator.proposal(hsv)
            cv2.imshow(WINDOW, calibrator.render(frame, hsv, proposal, stale))
            key = cv2.waitKey(15) & 0xFF
            if key in (13, 10):
                if calibrator.try_save(proposal, stale):
                    break
            elif key in (ord('r'), ord('R')):
                calibrator.reset()
                print('[hsv] clicks reset')
            elif key in (27, ord('q'), ord('Q')):
                print('[hsv] cancelled; YAML untouched.')
                return 1
            if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                print('[hsv] window closed; YAML untouched.')
                return 1
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.try_shutdown()
    # Only reached after a successful local save; the window is closed so an
    # SSH password prompt (if any) is answered in this terminal.
    return deploy_to_pinky(args)


def banner(*lines):
    rule = '=' * 50
    print('\n'.join([rule, *lines, rule]))


def deploy_to_pinky(args):
    if args.no_deploy:
        banner('LOCAL CALIBRATION SAVED (--no-deploy)',
               'Pinky config: NOT updated',
               'Pinky still runs its OLD HSV values')
        return 0
    try:
        host, source = hsv_deploy.resolve_host()
    except ValueError as exc:
        ok, reason, host = False, str(exc), '?'
    else:
        print(f'Pinky deploy target: {host}  (from {source})')
        ok, reason = hsv_deploy.deploy(args.config, host)
    if ok:
        print(f'[deploy] {reason}')
        banner('HSV CALIBRATION READY',
               'Laptop config: updated',
               'Pinky config: updated + verified',
               f'Pinky target: {host}')
        return 0
    print(f'[deploy] FAILED: {reason}', file=sys.stderr)
    banner('LOCAL CALIBRATION SAVED',
           'PINKY DEPLOY FAILED',
           'DO NOT START THE COMPETITION YET',
           f'Pinky target: {host}')
    return 4


def main(argv=None):
    try:
        return run(parse_args(sys.argv[1:] if argv is None else argv))
    except KeyboardInterrupt:
        print('\n[hsv] interrupted; YAML untouched.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
