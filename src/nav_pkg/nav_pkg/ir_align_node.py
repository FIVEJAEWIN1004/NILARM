"""Low-speed, service-gated final alignment using Pinky floor IR sensors."""

from enum import Enum
from typing import Optional, Tuple

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Bool, Float32MultiArray, String
from std_srvs.srv import SetBool


class AlignState(Enum):
    INACTIVE = 'inactive'
    SEARCHING = 'searching'
    ALIGNING = 'aligning'
    CENTER_HOLD = 'center_hold'
    ALIGNED = 'aligned'
    ERROR = 'error'


class IrAlignNode(Node):
    """Align IR2 over a dark target with IR1 and IR3 on bright floor."""

    def __init__(self):
        super().__init__('ir_align_node')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('read_rate_hz', 20.0)
        self.declare_parameter('dark_threshold', -1.0)
        self.declare_parameter('dark_is_low', True)
        self.declare_parameter('linear_speed', 0.015)
        self.declare_parameter('search_speed', 0.010)
        self.declare_parameter('angular_speed', 0.10)
        self.declare_parameter('debounce_samples', 3)
        self.declare_parameter('center_hold_sec', 0.5)
        self.declare_parameter('max_alignment_sec', 8.0)
        self.declare_parameter('all_dark_is_centered', False)
        self.declare_parameter('auto_start', False)

        self._validate_parameters()

        cmd_vel_topic = str(self.get_parameter('cmd_vel_topic').value)
        self.cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.values_pub = self.create_publisher(
            Float32MultiArray, '/ir_align/values', 10)
        self.status_pub = self.create_publisher(String, '/ir_align/status', 10)
        latched_qos = QoSProfile(depth=1)
        latched_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.aligned_pub = self.create_publisher(
            Bool, '/ir_align/aligned', latched_qos)
        self.enable_srv = self.create_service(
            SetBool, '/ir_align/enable', self._enable_callback)

        self.ir = self._create_ir_sensor()
        self.state = AlignState.INACTIVE
        self.active = False
        self.started_at = None
        self.center_since = None
        self.last_pattern: Optional[Tuple[bool, bool, bool]] = None
        self.pattern_count = 0

        period = 1.0 / float(self.get_parameter('read_rate_hz').value)
        self.timer = self.create_timer(period, self._timer_callback)
        self._publish_aligned(False)
        self._publish_status('inactive')

        if bool(self.get_parameter('auto_start').value):
            if self._ready_to_enable():
                self._start_alignment()
            else:
                self.get_logger().error(
                    'auto_start requested, but IR hardware/threshold is not ready')

    def _validate_parameters(self):
        linear = float(self.get_parameter('linear_speed').value)
        search = float(self.get_parameter('search_speed').value)
        angular = float(self.get_parameter('angular_speed').value)
        rate = float(self.get_parameter('read_rate_hz').value)
        debounce = int(self.get_parameter('debounce_samples').value)
        hold = float(self.get_parameter('center_hold_sec').value)
        timeout = float(self.get_parameter('max_alignment_sec').value)

        if not 0.0 <= linear <= 0.03:
            raise ValueError('linear_speed must be within [0.0, 0.03] m/s')
        if not 0.0 <= search <= 0.03:
            raise ValueError('search_speed must be within [0.0, 0.03] m/s')
        if not 0.0 <= angular <= 0.15:
            raise ValueError('angular_speed must be within [0.0, 0.15] rad/s')
        if rate <= 0.0 or debounce < 1 or hold <= 0.0 or timeout <= 0.0:
            raise ValueError('timing and debounce parameters must be positive')

    def _create_ir_sensor(self):
        try:
            from pinkylib import IR  # Imported only on Pinky hardware.
            return IR()
        except Exception as exc:  # Hardware module is absent on development PC.
            self.get_logger().error(f'Unable to initialize pinkylib.IR: {exc}')
            return None

    def _ready_to_enable(self) -> bool:
        threshold = float(self.get_parameter('dark_threshold').value)
        if self.ir is None:
            return False
        if threshold < 0.0:
            self.get_logger().error(
                'dark_threshold is unset; calibrate bright/dark values first')
            return False
        return True

    def _enable_callback(self, request, response):
        if request.data:
            if not self._ready_to_enable():
                response.success = False
                response.message = 'IR unavailable or dark_threshold is unset'
                return response
            self._start_alignment()
            response.success = True
            response.message = 'IR alignment enabled'
            return response

        self._stop_alignment(AlignState.INACTIVE, 'disabled')
        response.success = True
        response.message = 'IR alignment disabled and zero velocity published'
        return response

    def _start_alignment(self):
        self.active = True
        self.state = AlignState.SEARCHING
        self.started_at = self.get_clock().now()
        self.center_since = None
        self.last_pattern = None
        self.pattern_count = 0
        self._publish_aligned(False)
        self._publish_status('searching')
        self.get_logger().info('IR final alignment started')

    def _stop_alignment(self, state: AlignState, status: str):
        self._publish_twist(0.0, 0.0)
        self.active = False
        self.state = state
        self.center_since = None
        self._publish_status(status)
        self._publish_aligned(state == AlignState.ALIGNED)

    def _timer_callback(self):
        if self.ir is None:
            return

        try:
            raw = self.ir.read_ir()
            values = tuple(float(value) for value in raw) if raw is not None else ()
            if len(values) != 3:
                raise ValueError(f'expected three IR values, got {raw!r}')
        except Exception as exc:
            if self.active:
                self.get_logger().error(f'IR read failed: {exc}')
                self._stop_alignment(AlignState.ERROR, 'sensor_error')
            return

        values_msg = Float32MultiArray()
        values_msg.data = list(values)
        self.values_pub.publish(values_msg)

        if not self.active:
            return

        elapsed = (self.get_clock().now() - self.started_at).nanoseconds / 1e9
        if elapsed >= float(self.get_parameter('max_alignment_sec').value):
            self.get_logger().error('IR alignment timed out; stopping')
            self._stop_alignment(AlignState.ERROR, 'timeout')
            return

        pattern = tuple(self._is_dark(value) for value in values)
        if pattern != self.last_pattern:
            self.last_pattern = pattern
            self.pattern_count = 1
            # Do not continue the command selected for the previous pattern
            # while the new sensor state is being debounced.
            self._publish_twist(0.0, 0.0)
            return

        self.pattern_count += 1
        if self.pattern_count < int(self.get_parameter('debounce_samples').value):
            self._publish_twist(0.0, 0.0)
            return

        self._control(pattern)

    def _is_dark(self, value: float) -> bool:
        threshold = float(self.get_parameter('dark_threshold').value)
        if bool(self.get_parameter('dark_is_low').value):
            return value <= threshold
        return value >= threshold

    def _control(self, pattern: Tuple[bool, bool, bool]):
        left_dark, center_dark, right_dark = pattern
        centered = (not left_dark and center_dark and not right_dark)
        if bool(self.get_parameter('all_dark_is_centered').value):
            centered = centered or all(pattern)

        if centered:
            self._publish_twist(0.0, 0.0)
            if self.center_since is None:
                self.center_since = self.get_clock().now()
                self.state = AlignState.CENTER_HOLD
                self._publish_status('center_hold')
                return
            held = (self.get_clock().now() - self.center_since).nanoseconds / 1e9
            if held >= float(self.get_parameter('center_hold_sec').value):
                self.get_logger().info('IR center condition held; alignment complete')
                self._stop_alignment(AlignState.ALIGNED, 'aligned')
            return

        self.center_since = None
        linear = float(self.get_parameter('linear_speed').value)
        angular = float(self.get_parameter('angular_speed').value)
        self.state = AlignState.ALIGNING
        self._publish_status('aligning')

        if left_dark and not right_dark:
            self._publish_twist(linear, -angular)  # Arc right.
        elif right_dark and not left_dark:
            self._publish_twist(linear, angular)  # Arc left.
        elif center_dark:
            # Ambiguous broad target: creep forward until an edge pattern appears.
            self._publish_twist(
                float(self.get_parameter('search_speed').value), 0.0)
        elif not any(pattern):
            self.state = AlignState.SEARCHING
            self._publish_status('searching')
            self._publish_twist(
                float(self.get_parameter('search_speed').value), 0.0)
        else:
            self.get_logger().warn(f'ambiguous IR pattern {pattern}; stopping')
            self._publish_twist(0.0, 0.0)

    def _publish_twist(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = max(-0.03, min(0.03, linear_x))
        msg.angular.z = max(-0.15, min(0.15, angular_z))
        self.cmd_pub.publish(msg)

    def _publish_status(self, status: str):
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)

    def _publish_aligned(self, aligned: bool):
        msg = Bool()
        msg.data = aligned
        self.aligned_pub.publish(msg)

    def destroy_node(self):
        if hasattr(self, 'cmd_pub'):
            self._publish_twist(0.0, 0.0)
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = IrAlignNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
