#!/usr/bin/env python3

"""Low-speed lane-following controller driven by RoadModel."""

import time

from geometry_msgs.msg import Twist
from interfaces_pkg.msg import RoadModel
import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions


class LineFollower(Node):
    """Convert a valid road model into conservative velocity commands."""

    def __init__(self):
        super().__init__('line_follower')

        self.base_speed = float(
            self.declare_parameter('base_speed', 0.04).value
        )
        self.min_speed = float(
            self.declare_parameter('min_speed', 0.02).value
        )
        self.max_angular_speed = float(
            self.declare_parameter('max_angular_speed', 0.25).value
        )
        self.k_lateral = float(
            self.declare_parameter('k_lateral', 0.20).value
        )
        self.k_heading = float(
            self.declare_parameter('k_heading', -0.60).value
        )
        self.heading_deadband_rad = float(
            self.declare_parameter('heading_deadband_rad', 0.10).value
        )
        self.single_side_lateral_limit = float(
            self.declare_parameter('single_side_lateral_limit', 0.8).value
        )
        self.single_side_heading_limit_rad = float(
            self.declare_parameter(
                'single_side_heading_limit_rad', 0.7
            ).value
        )
        self.single_side_max_speed = float(
            self.declare_parameter('single_side_max_speed', 0.025).value
        )
        self.confidence_threshold = float(
            self.declare_parameter('confidence_threshold', 0.45).value
        )
        self.model_timeout = float(
            self.declare_parameter('model_timeout', 0.30).value
        )

        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(
            RoadModel,
            '/road/model',
            self.road_model_callback,
            10,
        )

        self.last_model_time = None
        self.last_log_time = 0.0
        self.last_stop_reason = 'WAITING_FOR_ROAD_MODEL'
        self.last_mode = None
        self.create_timer(0.05, self.safety_check)

        self.get_logger().info(
            'NILARM lane follower ready (waiting for valid /road/model) '
            f'base_speed={self.base_speed:.3f} min_speed={self.min_speed:.3f} '
            f'max_angular={self.max_angular_speed:.3f} '
            f'k_lateral={self.k_lateral:.3f} k_heading={self.k_heading:.3f} '
            f'heading_deadband={self.heading_deadband_rad:.3f} '
            f'single_side_lateral_limit={self.single_side_lateral_limit:.3f} '
            f'single_side_heading_limit={self.single_side_heading_limit_rad:.3f} '
            f'single_side_max_speed={self.single_side_max_speed:.3f} '
            f'confidence_threshold={self.confidence_threshold:.3f} '
            f'model_timeout={self.model_timeout:.3f}'
        )

    @staticmethod
    def _mode(msg):
        if msg.left_detected and msg.right_detected:
            return 'BOTH'
        if msg.left_detected:
            return 'LEFT ONLY'
        if msg.right_detected:
            return 'RIGHT ONLY'
        return 'LOST'

    def _log_control(
        self,
        mode,
        msg,
        normalized_lateral_error,
        effective_heading,
        lateral_term,
        heading_term,
        linear_x,
        angular_z,
        stop_reason,
        force=False,
    ):
        now = time.monotonic()
        if not force and now - self.last_log_time < 1.0:
            return
        self.last_log_time = now
        self.get_logger().info(
            f'MODE={mode} '
            f'lateral_error_px={msg.lateral_error_px:.1f} '
            f'normalized_lateral_error={normalized_lateral_error:.3f} '
            f'heading_error_rad={msg.heading_error_rad:.3f} '
            f'effective_heading_rad={effective_heading:.3f} '
            f'lateral_term={lateral_term:.3f} '
            f'heading_term={heading_term:.3f} '
            f'confidence={msg.confidence:.3f} '
            f'linear_x={linear_x:.3f} angular_z={angular_z:.3f} '
            f'STOP reason={stop_reason}'
        )

    def road_model_callback(self, msg):
        self.last_model_time = time.monotonic()
        mode = self._mode(msg)
        mode_changed = mode != self.last_mode
        self.last_mode = mode
        half_lane_width = max(1.0, 0.5 * float(msg.lane_width_px))
        normalized_lateral_error = float(
            msg.lateral_error_px
        ) / half_lane_width
        raw_heading = float(msg.heading_error_rad)
        effective_heading = 0.0
        if abs(raw_heading) > self.heading_deadband_rad:
            heading_sign = 1.0 if raw_heading > 0.0 else -1.0
            effective_heading = heading_sign * (
                abs(raw_heading) - self.heading_deadband_rad
            )
        lateral_term = self.k_lateral * normalized_lateral_error
        heading_term = self.k_heading * effective_heading

        stop_reason = 'NONE'
        if not msg.center_valid:
            stop_reason = 'CENTER_INVALID'
        elif mode == 'LOST':
            stop_reason = 'LOST'
        elif msg.confidence < self.confidence_threshold:
            stop_reason = 'LOW_CONFIDENCE'
        elif mode != 'BOTH' and (
            abs(normalized_lateral_error) > self.single_side_lateral_limit
        ):
            stop_reason = 'SINGLE_SIDE_LATERAL_GATE'
        elif mode != 'BOTH' and (
            abs(raw_heading) > self.single_side_heading_limit_rad
        ):
            stop_reason = 'SINGLE_SIDE_HEADING_GATE'

        if stop_reason != 'NONE':
            self.stop_robot()
            force_log = stop_reason != self.last_stop_reason or mode_changed
            self.last_stop_reason = stop_reason
            self._log_control(
                mode, msg, normalized_lateral_error, effective_heading,
                lateral_term, heading_term, 0.0, 0.0, stop_reason,
                force=force_log,
            )
            return

        angular_z = lateral_term + heading_term
        angular_z = max(
            -self.max_angular_speed,
            min(self.max_angular_speed, angular_z),
        )

        angular_ratio = min(
            1.0,
            abs(angular_z) / max(1e-6, self.max_angular_speed),
        )
        linear_x = self.base_speed - angular_ratio * (
            self.base_speed - self.min_speed
        )
        linear_x = max(self.min_speed, min(self.base_speed, linear_x))
        if mode != 'BOTH':
            linear_x = min(linear_x, self.single_side_max_speed)

        command = Twist()
        command.linear.x = linear_x
        command.angular.z = angular_z
        self.cmd_vel_publisher.publish(command)

        self.last_stop_reason = 'NONE'
        self._log_control(
            mode, msg, normalized_lateral_error, effective_heading,
            lateral_term, heading_term, linear_x, angular_z, 'NONE',
            force=mode_changed,
        )

    def safety_check(self):
        if self.last_model_time is None:
            self.stop_robot()
            return

        elapsed = time.monotonic() - self.last_model_time
        if elapsed <= self.model_timeout:
            return

        self.stop_robot()
        if self.last_stop_reason != 'MODEL_TIMEOUT':
            self.last_stop_reason = 'MODEL_TIMEOUT'
            self.get_logger().warning(
                f'MODE=LOST lateral_error_px=0.0 '
                f'normalized_lateral_error=0.000 heading_error_rad=0.000 '
                f'effective_heading_rad=0.000 lateral_term=0.000 '
                f'heading_term=0.000 '
                f'confidence=0.000 linear_x=0.000 angular_z=0.000 '
                f'STOP reason=MODEL_TIMEOUT elapsed={elapsed:.3f}s'
            )

    def stop_robot(self):
        self.cmd_vel_publisher.publish(Twist())

    def publish_stop_sequence(self):
        self.get_logger().info('Stopping lane follower; publishing zero velocity')
        for _ in range(10):
            self.stop_robot()
            time.sleep(0.05)


def main(args=None):
    # Keep the context alive when Ctrl+C raises KeyboardInterrupt so the final
    # zero-velocity sequence can be published before shutdown.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = LineFollower()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.publish_stop_sequence()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
