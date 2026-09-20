"""Exclusive command arbiter for HSV straight driving and Nav2 curves."""

from enum import Enum
from typing import Optional, Tuple

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_srvs.srv import SetBool


class DriveMode(Enum):
    LINE_FOLLOW = 'LINE_FOLLOW'
    NAV2_CURVE = 'NAV2_CURVE'
    STOP_ALIGN = 'STOP_ALIGN'
    GOAL = 'GOAL'


class StraightNavController(Node):
    """Select, but never combine, HSV line control and Nav2 commands."""

    def __init__(self):
        super().__init__('camera_drive_controller')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('nav_cmd_topic', '/cmd_vel_nav_smoothed')
        self.declare_parameter('output_cmd_topic', '/cmd_vel')
        self.declare_parameter('debug_image_topic', '/vision_drive/debug_image')
        self.declare_parameter('enabled', False)
        self.declare_parameter('initial_mode', 'LINE_FOLLOW')
        self.declare_parameter('roi_top', 0.62)
        self.declare_parameter('roi_bottom', 0.94)
        self.declare_parameter('boundary_hsv_lower', [5, 35, 35])
        self.declare_parameter('boundary_hsv_upper', [35, 255, 230])
        self.declare_parameter('morph_kernel', 5)
        self.declare_parameter('min_boundary_area', 250.0)
        self.declare_parameter('left_search_max_ratio', 0.70)
        self.declare_parameter('left_offset_cm', 8.0)
        self.declare_parameter('left_offset_pixels', -1.0)
        self.declare_parameter('pixels_per_cm', 0.0)
        self.declare_parameter('kp', 0.004)
        self.declare_parameter('deadband_pixels', 5.0)
        self.declare_parameter('linear_speed', 0.05)
        self.declare_parameter('angular_limit', 0.20)
        self.declare_parameter('image_timeout_sec', 0.5)
        self.declare_parameter('nav_cmd_timeout_sec', 0.5)
        self.declare_parameter('mode_switch_hold_sec', 0.20)

        self._validate_parameters()
        self.bridge = CvBridge()
        self.enabled = bool(self.get_parameter('enabled').value)
        self.mode = DriveMode(
            str(self.get_parameter('initial_mode').value).upper())
        self.last_image_time = None
        self.last_nav_cmd_time = None
        self.mode_changed_at = self.get_clock().now()
        self.last_linear = 0.0
        self.last_angular = 0.0
        self.last_error: Optional[float] = None

        self.cmd_pub = self.create_publisher(
            Twist, str(self.get_parameter('output_cmd_topic').value), 10)
        self.debug_pub = self.create_publisher(
            Image, str(self.get_parameter('debug_image_topic').value), 10)
        self.state_pub = self.create_publisher(String, '/vision_drive/state', 10)
        self.create_subscription(
            Image, str(self.get_parameter('camera_topic').value),
            self._image_callback, 10)
        self.create_subscription(
            Twist, str(self.get_parameter('nav_cmd_topic').value),
            self._nav_cmd_callback, 10)
        self.create_subscription(
            String, '/vision_drive/mode_cmd', self._mode_callback, 10)
        self.create_service(
            SetBool, '/vision_drive/enable', self._enable_callback)
        self.watchdog = self.create_timer(0.1, self._watchdog_callback)
        self._publish_state()

    def _validate_parameters(self):
        if not 0.0 <= float(self.get_parameter('linear_speed').value) <= 0.05:
            raise ValueError('linear_speed must be within [0.0, 0.05] m/s')
        angular = float(self.get_parameter('angular_limit').value)
        if not 0.0 < angular <= 0.30:
            raise ValueError('angular_limit must be within (0.0, 0.30] rad/s')
        top = float(self.get_parameter('roi_top').value)
        bottom = float(self.get_parameter('roi_bottom').value)
        if not 0.0 <= top < bottom <= 1.0:
            raise ValueError('ROI must satisfy 0 <= roi_top < roi_bottom <= 1')
        for suffix in ('lower', 'upper'):
            values = self.get_parameter(f'boundary_hsv_{suffix}').value
            if len(values) != 3:
                raise ValueError('each boundary HSV limit must have 3 values')
        try:
            DriveMode(str(self.get_parameter('initial_mode').value).upper())
        except ValueError as exc:
            raise ValueError('invalid initial_mode') from exc

    def _image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().error(f'image conversion failed: {exc}')
            if self.enabled and self.mode == DriveMode.LINE_FOLLOW:
                self._publish_zero()
            return

        now = self.get_clock().now()
        self.last_image_time = now
        debug = frame.copy()
        mask = self._boundary_mask(frame)
        observation = self._left_boundary(mask, debug)
        height, width = frame.shape[:2]
        image_center = width // 2
        offset_pixels = self._calibrated_offset_pixels()
        self.last_error = None
        line_angular = 0.0

        if observation is not None and offset_pixels is not None:
            boundary_x, sample_y = observation
            target_x = int(round(boundary_x + offset_pixels))
            error = float(target_x - image_center)
            self.last_error = error
            top = int(height * float(self.get_parameter('roi_top').value))
            bottom = int(height * float(self.get_parameter('roi_bottom').value))
            cv2.line(debug, (boundary_x, top), (boundary_x, bottom),
                     (0, 255, 255), 2)
            cv2.line(debug, (target_x, top), (target_x, bottom),
                     (0, 255, 0), 2)
            cv2.circle(debug, (target_x, sample_y), 6, (0, 255, 0), -1)
            if abs(error) > float(
                    self.get_parameter('deadband_pixels').value):
                # Image x is positive right; ROS angular.z is positive left.
                line_angular = -float(self.get_parameter('kp').value) * error
                limit = float(self.get_parameter('angular_limit').value)
                line_angular = max(-limit, min(limit, line_angular))

        if self.enabled and self.mode == DriveMode.LINE_FOLLOW:
            if self._in_switch_hold(now):
                self._publish_zero()
            elif observation is None or offset_pixels is None:
                self._publish_zero()
            else:
                self._publish_line_command(line_angular)

        cv2.line(debug, (image_center, 0), (image_center, height),
                 (255, 0, 255), 1)
        self._draw_debug(debug)
        debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding='bgr8')
        debug_msg.header = msg.header
        self.debug_pub.publish(debug_msg)

    def _boundary_mask(self, frame: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array(
            self.get_parameter('boundary_hsv_lower').value, dtype=np.uint8)
        upper = np.array(
            self.get_parameter('boundary_hsv_upper').value, dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        size = max(1, int(self.get_parameter('morph_kernel').value) | 1)
        kernel = np.ones((size, size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    def _left_boundary(
            self, mask: np.ndarray, debug: np.ndarray
            ) -> Optional[Tuple[int, int]]:
        height, width = mask.shape
        top = int(height * float(self.get_parameter('roi_top').value))
        bottom = int(height * float(self.get_parameter('roi_bottom').value))
        max_x = int(
            width * float(self.get_parameter('left_search_max_ratio').value))
        roi = mask[top:bottom, :max_x]
        cv2.rectangle(debug, (0, top), (max_x, bottom), (255, 255, 0), 1)
        contours, _ = cv2.findContours(
            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = float(self.get_parameter('min_boundary_area').value)
        candidates = [c for c in contours if cv2.contourArea(c) >= min_area]
        if not candidates:
            return None
        contour = max(candidates, key=cv2.contourArea)
        shifted = contour.copy()
        shifted[:, 0, 1] += top
        cv2.drawContours(debug, [shifted], -1, (0, 165, 255), 2)
        points = shifted[:, 0, :]
        # Road-facing side of a colored region on the left is its right edge.
        boundary_x = int(np.percentile(points[:, 0], 95))
        sample_y = int(np.median(points[:, 1]))
        return boundary_x, sample_y

    def _calibrated_offset_pixels(self) -> Optional[float]:
        direct = float(self.get_parameter('left_offset_pixels').value)
        if direct > 0.0:
            return direct
        pixels_per_cm = float(self.get_parameter('pixels_per_cm').value)
        if pixels_per_cm > 0.0:
            return pixels_per_cm * float(
                self.get_parameter('left_offset_cm').value)
        return None

    def _nav_cmd_callback(self, nav_cmd: Twist):
        now = self.get_clock().now()
        self.last_nav_cmd_time = now
        if not self.enabled or self.mode != DriveMode.NAV2_CURVE:
            return
        if self._in_switch_hold(now):
            self._publish_zero()
            return
        # Exclusive selection: forward Nav2 exactly, without vision correction.
        self.cmd_pub.publish(nav_cmd)
        self.last_linear = nav_cmd.linear.x
        self.last_angular = nav_cmd.angular.z

    def _mode_callback(self, msg: String):
        requested = msg.data.strip().upper()
        try:
            mode = DriveMode(requested)
        except ValueError:
            self.get_logger().error(
                f'ignored invalid mode {msg.data!r}; expected '
                'LINE_FOLLOW, NAV2_CURVE, STOP_ALIGN, or GOAL')
            return
        if mode == self.mode:
            return
        self._publish_zero()
        self.mode = mode
        self.mode_changed_at = self.get_clock().now()
        self._publish_state()
        self.get_logger().info(f'drive mode changed to {mode.value}')

    def _enable_callback(self, request, response):
        self._publish_zero()
        self.enabled = bool(request.data)
        self.mode_changed_at = self.get_clock().now()
        self._publish_state()
        response.success = True
        response.message = (
            f'controller enabled in {self.mode.value}' if self.enabled
            else 'controller disabled and zero velocity sent')
        return response

    def _watchdog_callback(self):
        if not self.enabled:
            return
        now = self.get_clock().now()
        if self.mode == DriveMode.LINE_FOLLOW:
            if self._is_stale(
                    now, self.last_image_time,
                    float(self.get_parameter('image_timeout_sec').value)):
                self._publish_zero()
        elif self.mode == DriveMode.NAV2_CURVE:
            if self._is_stale(
                    now, self.last_nav_cmd_time,
                    float(self.get_parameter('nav_cmd_timeout_sec').value)):
                self._publish_zero()
        else:
            self._publish_zero()

    def _in_switch_hold(self, now) -> bool:
        elapsed = (now - self.mode_changed_at).nanoseconds / 1e9
        return elapsed < float(
            self.get_parameter('mode_switch_hold_sec').value)

    @staticmethod
    def _is_stale(now, stamp, timeout: float) -> bool:
        return stamp is None or (now - stamp).nanoseconds / 1e9 > timeout

    def _publish_line_command(self, angular_z: float):
        msg = Twist()
        msg.linear.x = float(self.get_parameter('linear_speed').value)
        msg.angular.z = angular_z
        self.cmd_pub.publish(msg)
        self.last_linear = msg.linear.x
        self.last_angular = msg.angular.z

    def _publish_zero(self):
        self.cmd_pub.publish(Twist())
        self.last_linear = 0.0
        self.last_angular = 0.0

    def _publish_state(self):
        msg = String()
        msg.data = self.mode.value if self.enabled else 'DISABLED'
        self.state_pub.publish(msg)

    def _draw_debug(self, image: np.ndarray):
        error_text = 'N/A' if self.last_error is None else f'{self.last_error:.1f}px'
        lines = [
            f'STATE={self.mode.value if self.enabled else "DISABLED"}',
            f'error={error_text}',
            f'linear={self.last_linear:.3f} m/s',
            f'angular={self.last_angular:.3f} rad/s',
        ]
        if self.mode == DriveMode.NAV2_CURVE:
            lines.append('vision angular=0.000 (Nav2 pass-through)')
        if self._calibrated_offset_pixels() is None:
            lines.append('OFFSET NOT CALIBRATED - LINE MOTION BLOCKED')
        for index, text in enumerate(lines):
            cv2.putText(image, text, (10, 25 + index * 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 255), 2)

    def destroy_node(self):
        if hasattr(self, 'cmd_pub'):
            self._publish_zero()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = StraightNavController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
