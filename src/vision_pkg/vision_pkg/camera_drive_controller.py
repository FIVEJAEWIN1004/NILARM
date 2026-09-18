"""Camera correction layer between Nav2 velocity smoothing and Pinky."""

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


class DriveState(Enum):
    DRIVE = 'drive'
    ALIGN_STOP = 'align_stop'
    STOP = 'stop'
    LOST = 'lost'


class CameraDriveController(Node):
    """Correct a Nav2 command using road and STOP observations."""

    def __init__(self):
        super().__init__('camera_drive_controller')

        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('nav_cmd_topic', '/cmd_vel_nav_smoothed')
        self.declare_parameter('output_cmd_topic', '/cmd_vel')
        self.declare_parameter('debug_image_topic', '/vision_drive/debug_image')
        self.declare_parameter('enabled', False)

        self.declare_parameter('near_roi_top', 0.68)
        self.declare_parameter('near_roi_bottom', 0.95)
        self.declare_parameter('far_roi_top', 0.43)
        self.declare_parameter('far_roi_bottom', 0.67)
        self.declare_parameter('road_hsv_lower', [0, 0, 120])
        self.declare_parameter('road_hsv_upper', [179, 95, 255])
        self.declare_parameter('stop_hsv_lower', [5, 45, 40])
        self.declare_parameter('stop_hsv_upper', [35, 255, 220])
        self.declare_parameter('morph_kernel', 5)
        self.declare_parameter('min_road_width_ratio', 0.18)
        self.declare_parameter('min_stop_area_ratio', 0.015)

        self.declare_parameter('center_kp', 0.22)
        self.declare_parameter('curve_kp', 0.14)
        self.declare_parameter('stop_kp', 0.25)
        self.declare_parameter('linear_speed', 0.05)
        self.declare_parameter('angular_limit', 0.30)
        self.declare_parameter('stop_align_speed', 0.018)
        self.declare_parameter('stop_distance', 0.12)
        self.declare_parameter('stop_center_tolerance', 0.06)
        self.declare_parameter('stop_hold_sec', 0.5)
        self.declare_parameter('stop_debounce_frames', 3)
        self.declare_parameter('image_timeout_sec', 0.5)
        self.declare_parameter('nav_cmd_timeout_sec', 0.5)
        self.declare_parameter('road_loss_timeout_sec', 0.7)

        self._validate_parameters()
        self.bridge = CvBridge()
        self.enabled = bool(self.get_parameter('enabled').value)
        self.state = DriveState.LOST
        self.last_image_time = None
        self.last_nav_cmd_time = None
        self.last_road_time = None
        self.stop_center_since = None
        self.near_error: Optional[float] = None
        self.far_error: Optional[float] = None
        self.stop_error: Optional[float] = None
        self.stop_close = False
        self.stop_close_count = 0

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
        self.create_service(
            SetBool, '/vision_drive/enable', self._enable_callback)
        self.watchdog = self.create_timer(0.1, self._watchdog_callback)
        self._publish_state()

    def _validate_parameters(self):
        linear = float(self.get_parameter('linear_speed').value)
        align = float(self.get_parameter('stop_align_speed').value)
        angular = float(self.get_parameter('angular_limit').value)
        if not 0.0 <= linear <= 0.05:
            raise ValueError('linear_speed must be within [0.0, 0.05] m/s')
        if not 0.0 <= align <= 0.05:
            raise ValueError('stop_align_speed must be within [0.0, 0.05] m/s')
        if not 0.0 < angular <= 0.30:
            raise ValueError('angular_limit must be within (0.0, 0.30] rad/s')
        for name in ('near_roi_top', 'near_roi_bottom', 'far_roi_top',
                     'far_roi_bottom', 'stop_distance'):
            value = float(self.get_parameter(name).value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f'{name} must be a normalized value in [0, 1]')
        near_top = float(self.get_parameter('near_roi_top').value)
        near_bottom = float(self.get_parameter('near_roi_bottom').value)
        far_top = float(self.get_parameter('far_roi_top').value)
        far_bottom = float(self.get_parameter('far_roi_bottom').value)
        if not (far_top < far_bottom <= near_top < near_bottom):
            raise ValueError('ROI order must be far < near and each top < bottom')
        if int(self.get_parameter('stop_debounce_frames').value) < 1:
            raise ValueError('stop_debounce_frames must be at least 1')
        for prefix in ('road', 'stop'):
            lower = self.get_parameter(f'{prefix}_hsv_lower').value
            upper = self.get_parameter(f'{prefix}_hsv_upper').value
            if len(lower) != 3 or len(upper) != 3:
                raise ValueError(f'{prefix} HSV limits must each contain 3 values')

    def _image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().error(f'image conversion failed: {exc}')
            return

        now = self.get_clock().now()
        self.last_image_time = now
        debug = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        road_mask = self._hsv_mask(hsv, 'road')
        stop_mask = self._hsv_mask(hsv, 'stop')

        height, width = frame.shape[:2]
        near = self._road_observation(road_mask, debug, 'near', (0, 255, 0))
        far = self._road_observation(road_mask, debug, 'far', (255, 255, 0))
        self.near_error = self._normalized_error(near, width)
        self.far_error = self._normalized_error(far, width)
        if near is not None:
            self.last_road_time = now

        stop = self._stop_observation(stop_mask, debug)
        self.stop_error = None
        self.stop_close = False
        if stop is not None:
            x, y, box_w, box_h, center_x = stop
            self.stop_error = (center_x - width / 2.0) / (width / 2.0)
            bottom_gap_ratio = max(0.0, (height - (y + box_h)) / height)
            close_now = bottom_gap_ratio <= float(
                self.get_parameter('stop_distance').value)
            self.stop_close_count = self.stop_close_count + 1 if close_now else 0
            self.stop_close = self.stop_close_count >= int(
                self.get_parameter('stop_debounce_frames').value)
            cv2.rectangle(debug, (x, y), (x + box_w, y + box_h),
                          (0, 0, 255), 2)
            cv2.circle(debug, (center_x, y + box_h // 2), 6,
                       (0, 0, 255), -1)
        else:
            self.stop_close_count = 0

        cv2.line(debug, (width // 2, 0), (width // 2, height),
                 (255, 0, 255), 1)
        label = f'{self.state.value} near={self.near_error} far={self.far_error}'
        cv2.putText(debug, label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 0, 255), 2)
        debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding='bgr8')
        debug_msg.header = msg.header
        self.debug_pub.publish(debug_msg)

    def _hsv_mask(self, hsv: np.ndarray, prefix: str) -> np.ndarray:
        lower = np.array(self.get_parameter(f'{prefix}_hsv_lower').value,
                         dtype=np.uint8)
        upper = np.array(self.get_parameter(f'{prefix}_hsv_upper').value,
                         dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        kernel_size = int(self.get_parameter('morph_kernel').value)
        kernel_size = max(1, kernel_size | 1)
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    def _road_observation(
            self, mask: np.ndarray, debug: np.ndarray, name: str,
            color: Tuple[int, int, int]) -> Optional[Tuple[int, int, int]]:
        height, width = mask.shape
        top = int(height * float(self.get_parameter(f'{name}_roi_top').value))
        bottom = int(
            height * float(self.get_parameter(f'{name}_roi_bottom').value))
        roi = mask[top:bottom, :]
        contours, _ = cv2.findContours(
            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.rectangle(debug, (0, top), (width - 1, bottom), color, 1)
        if not contours:
            return None

        candidates = []
        min_width = width * float(
            self.get_parameter('min_road_width_ratio').value)
        for contour in contours:
            x, y, box_w, box_h = cv2.boundingRect(contour)
            if box_w >= min_width:
                candidates.append((cv2.contourArea(contour), x, box_w, contour))
        if not candidates:
            return None
        _, x, box_w, contour = max(candidates, key=lambda item: item[0])
        shifted = contour.copy()
        shifted[:, 0, 1] += top
        cv2.drawContours(debug, [shifted], -1, color, 2)
        left = x
        right = x + box_w - 1
        center = (left + right) // 2
        row = (top + bottom) // 2
        cv2.line(debug, (left, row), (right, row), color, 3)
        cv2.circle(debug, (center, row), 6, color, -1)
        return left, right, center

    def _stop_observation(
            self, mask: np.ndarray, debug: np.ndarray
            ) -> Optional[Tuple[int, int, int, int, int]]:
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        contour = max(contours, key=cv2.contourArea)
        area_ratio = cv2.contourArea(contour) / float(mask.size)
        if area_ratio < float(self.get_parameter('min_stop_area_ratio').value):
            return None
        x, y, width, height = cv2.boundingRect(contour)
        return x, y, width, height, x + width // 2

    @staticmethod
    def _normalized_error(
            observation: Optional[Tuple[int, int, int]], width: int
            ) -> Optional[float]:
        if observation is None:
            return None
        return (observation[2] - width / 2.0) / (width / 2.0)

    def _nav_cmd_callback(self, nav_cmd: Twist):
        now = self.get_clock().now()
        self.last_nav_cmd_time = now
        if not self.enabled:
            return
        if self._is_stale(now, self.last_image_time,
                          float(self.get_parameter('image_timeout_sec').value)):
            self._set_state(DriveState.LOST)
            self._publish_zero()
            return

        if self.stop_error is not None and self.stop_close:
            self._align_stop(now)
            return

        if self.state == DriveState.STOP:
            self._publish_zero()
            return
        if self._is_stale(
                now, self.last_road_time,
                float(self.get_parameter('road_loss_timeout_sec').value)):
            self._set_state(DriveState.LOST)
            self._publish_zero()
            return

        self.stop_center_since = None
        self._set_state(DriveState.DRIVE)
        near = self.near_error if self.near_error is not None else 0.0
        far = self.far_error if self.far_error is not None else near
        # Image x grows to the right, while positive ROS angular.z turns left.
        center_correction = -float(
            self.get_parameter('center_kp').value) * near
        curve_correction = -float(
            self.get_parameter('curve_kp').value) * (far - near)
        angular = nav_cmd.angular.z + center_correction + curve_correction
        speed_limit = float(self.get_parameter('linear_speed').value)
        linear = max(0.0, min(speed_limit, nav_cmd.linear.x))
        self._publish_cmd(linear, angular)

    def _align_stop(self, now):
        self._set_state(DriveState.ALIGN_STOP)
        error = self.stop_error if self.stop_error is not None else 0.0
        tolerance = float(
            self.get_parameter('stop_center_tolerance').value)
        if abs(error) <= tolerance:
            self._publish_zero()
            if self.stop_center_since is None:
                self.stop_center_since = now
                return
            held = (now - self.stop_center_since).nanoseconds / 1e9
            if held >= float(self.get_parameter('stop_hold_sec').value):
                self._set_state(DriveState.STOP)
            return

        self.stop_center_since = None
        linear = float(self.get_parameter('stop_align_speed').value)
        angular = -float(self.get_parameter('stop_kp').value) * error
        self._publish_cmd(linear, angular)

    def _watchdog_callback(self):
        if not self.enabled:
            return
        now = self.get_clock().now()
        if self._is_stale(now, self.last_image_time,
                          float(self.get_parameter('image_timeout_sec').value)):
            self._set_state(DriveState.LOST)
            self._publish_zero()
            return
        if self._is_stale(
                now, self.last_nav_cmd_time,
                float(self.get_parameter('nav_cmd_timeout_sec').value)):
            self._set_state(DriveState.LOST)
            self._publish_zero()

    def _enable_callback(self, request, response):
        self.enabled = bool(request.data)
        self.stop_center_since = None
        self.stop_close_count = 0
        if self.enabled:
            self._set_state(DriveState.LOST)
            response.message = 'vision correction enabled; waiting for fresh inputs'
        else:
            self._publish_zero()
            self._set_state(DriveState.LOST)
            response.message = 'vision correction disabled and zero velocity sent'
        response.success = True
        return response

    @staticmethod
    def _is_stale(now, stamp, timeout: float) -> bool:
        return stamp is None or (now - stamp).nanoseconds / 1e9 > timeout

    def _publish_cmd(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = max(0.0, min(0.05, linear_x))
        limit = float(self.get_parameter('angular_limit').value)
        msg.angular.z = max(-limit, min(limit, angular_z))
        self.cmd_pub.publish(msg)

    def _publish_zero(self):
        self._publish_cmd(0.0, 0.0)

    def _set_state(self, state: DriveState):
        if state != self.state:
            self.state = state
            self._publish_state()

    def _publish_state(self):
        msg = String()
        msg.data = self.state.value
        self.state_pub.publish(msg)

    def destroy_node(self):
        if hasattr(self, 'cmd_pub') and self.enabled:
            self._publish_zero()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraDriveController()
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
