import math
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions

from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped


class OdomDriveTest(Node):

    def __init__(self):
        super().__init__('odom_drive_test')

        # ==========================================
        # 주행 설정
        # ==========================================

        # 목표 이동거리
        # 0.50 m = 50 cm
        self.target_distance = 0.50

        # 직진 속도
        # 0.02 m/s = 초당 2 cm
        self.linear_speed = 0.02

        # ★ 장애물 즉시 정지 거리
        # 0.30 m = 30 cm
        self.obstacle_distance = 0.30

        # ==========================================
        # 위치 상태
        # ==========================================

        self.start_x = None
        self.start_y = None

        self.current_x = None
        self.current_y = None

        # ==========================================
        # LiDAR 상태
        # ==========================================

        self.front_distance = None

        # ==========================================
        # 프로그램 상태
        # ==========================================

        self.finished = False
        self.stopping = False

        # ==========================================
        # /odom Subscriber
        # ==========================================

        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            qos_profile_sensor_data
        )

        # ==========================================
        # /scan Subscriber
        # ==========================================

        self.scan_subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )

        # ==========================================
        # /cmd_vel Publisher
        # ==========================================

        self.cmd_publisher = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )

        self.get_logger().info(
            '================================'
        )

        self.get_logger().info(
            'NILARM SAFE ODOM DRIVE STARTED'
        )

        self.get_logger().info(
            f'Target distance : '
            f'{self.target_distance:.2f} m'
        )

        self.get_logger().info(
            f'Speed           : '
            f'{self.linear_speed:.2f} m/s'
        )

        self.get_logger().info(
            f'Obstacle stop   : '
            f'{self.obstacle_distance:.2f} m'
        )

        self.get_logger().info(
            '================================'
        )

    # ==============================================
    # LiDAR callback
    # ==============================================

    def scan_callback(self, msg):

        if self.finished or self.stopping:
            return

        ranges = msg.ranges

        # 정면 ±30도
        front_indices = (
            list(range(0, 31))
            + list(range(330, 360))
        )

        valid_ranges = []

        for i in front_indices:

            if i >= len(ranges):
                continue

            distance = ranges[i]

            # 유효한 LiDAR 값만 사용
            if (
                math.isfinite(distance)
                and distance >= 0.12
                and distance <= 3.5
            ):
                valid_ranges.append(distance)

        # 정면에서 가장 가까운 장애물
        if valid_ranges:

            self.front_distance = min(
                valid_ranges
            )

        else:

            self.front_distance = None

    # ==============================================
    # ODOM callback
    # ==============================================

    def odom_callback(self, msg):

        if self.finished or self.stopping:
            return

        # ==========================================
        # LiDAR 데이터가 없으면 출발 금지
        # ==========================================

        if self.front_distance is None:

            self.publish_zero()

            self.get_logger().warn(
                'WAITING FOR LIDAR -> STOP'
            )

            return

        # ==========================================
        # 현재 위치
        # ==========================================

        self.current_x = (
            msg.pose.pose.position.x
        )

        self.current_y = (
            msg.pose.pose.position.y
        )

        # ==========================================
        # 시작 위치 저장
        # ==========================================

        if self.start_x is None:

            self.start_x = self.current_x
            self.start_y = self.current_y

            self.get_logger().info(
                f'START POSITION | '
                f'X:{self.start_x:.3f} | '
                f'Y:{self.start_y:.3f}'
            )

            # 첫 odom에서는 출발하지 않음
            self.publish_zero()

            return

        # ==========================================
        # 이동거리 계산
        # ==========================================

        dx = (
            self.current_x
            - self.start_x
        )

        dy = (
            self.current_y
            - self.start_y
        )

        distance = math.sqrt(
            dx * dx
            + dy * dy
        )

        # ==========================================
        # ★ 1순위 안전조건
        #
        # 정면 장애물 30cm 이내
        # → 즉시 안전정지
        # ==========================================

        if (
            self.front_distance
            <= self.obstacle_distance
        ):

            self.finished = True

            self.get_logger().error(
                '================================'
            )

            self.get_logger().error(
                f'OBSTACLE DETECTED: '
                f'{self.front_distance:.3f} m'
            )

            self.get_logger().error(
                '30cm SAFETY STOP!'
            )

            self.get_logger().error(
                '================================'
            )

            self.emergency_stop()

            return

        # ==========================================
        # 목표거리 50cm 도달
        # ==========================================

        if distance >= self.target_distance:

            self.finished = True

            self.get_logger().info(
                '================================'
            )

            self.get_logger().info(
                f'TARGET REACHED: '
                f'{distance:.3f} m'
            )

            self.get_logger().info(
                'STOPPING ROBOT'
            )

            self.get_logger().info(
                '================================'
            )

            self.emergency_stop()

            return

        # ==========================================
        # 안전 + 목표거리 전
        # → 직진
        # ==========================================

        cmd = self.make_cmd()

        cmd.twist.linear.x = (
            self.linear_speed
        )

        cmd.twist.angular.z = 0.0

        self.cmd_publisher.publish(cmd)

        # ==========================================
        # 상태 출력
        # ==========================================

        self.get_logger().info(
            f'DIST:{distance:.3f}/'
            f'{self.target_distance:.3f}m | '
            f'FRONT:{self.front_distance:.3f}m | '
            f'X:{self.current_x:.3f} | '
            f'Y:{self.current_y:.3f}'
        )

    # ==============================================
    # TwistStamped 메시지 생성
    # ==============================================

    def make_cmd(self):

        cmd = TwistStamped()

        cmd.header.stamp = (
            self.get_clock().now().to_msg()
        )

        cmd.header.frame_id = 'base_link'

        # 모든 속도를 0으로 초기화
        cmd.twist.linear.x = 0.0
        cmd.twist.linear.y = 0.0
        cmd.twist.linear.z = 0.0

        cmd.twist.angular.x = 0.0
        cmd.twist.angular.y = 0.0
        cmd.twist.angular.z = 0.0

        return cmd

    # ==============================================
    # 일반 정지 명령
    # ==============================================

    def publish_zero(self):

        if not rclpy.ok():
            return

        stop_msg = self.make_cmd()

        stop_msg.twist.linear.x = 0.0
        stop_msg.twist.angular.z = 0.0

        self.cmd_publisher.publish(
            stop_msg
        )

    # ==============================================
    # ★ 확실한 안전 정지
    # ==============================================

    def emergency_stop(self):

        if self.stopping:
            return

        self.stopping = True

        self.get_logger().warn(
            'EMERGENCY STOP'
        )

        self.get_logger().warn(
            'Sending ZERO velocity...'
        )

        # 약 2초 동안
        # 0속도를 반복해서 publish
        #
        # 중요:
        # 여기서는 rclpy.spin_once()를 사용하지 않음.
        #
        # callback 안에서 이 함수가 호출될 수 있기 때문에
        # spin_once()를 다시 호출하면
        #
        # RuntimeError:
        # Executor is already spinning
        #
        # 오류가 발생할 수 있음.

        for _ in range(40):

            if not rclpy.ok():
                break

            stop_msg = self.make_cmd()

            stop_msg.twist.linear.x = 0.0
            stop_msg.twist.angular.z = 0.0

            self.cmd_publisher.publish(
                stop_msg
            )

            time.sleep(0.05)

        self.get_logger().warn(
            'ROBOT STOPPED'
        )


# ==================================================
# MAIN
# ==================================================

def main(args=None):

    # ==============================================
    # Ctrl+C를 우리가 직접 처리
    # ==============================================

    rclpy.init(
        args=args,
        signal_handler_options=(
            SignalHandlerOptions.NO
        )
    )

    node = OdomDriveTest()

    shutdown_requested = False

    # ==============================================
    # Ctrl+C handler
    # ==============================================

    def signal_handler(sig, frame):

        nonlocal shutdown_requested

        if shutdown_requested:
            return

        shutdown_requested = True

        print(
            '\nCTRL+C detected!'
        )

        # ROS context가 살아있는 동안
        # 먼저 확실하게 정지
        node.emergency_stop()

    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    try:

        while (
            rclpy.ok()
            and not shutdown_requested
            and not node.finished
        ):

            rclpy.spin_once(
                node,
                timeout_sec=0.1
            )

    finally:

        # 어떤 이유로 종료되더라도
        # 마지막 안전정지
        if (
            rclpy.ok()
            and not node.stopping
        ):

            node.emergency_stop()

        node.destroy_node()

        if rclpy.ok():

            rclpy.shutdown()


if __name__ == '__main__':
    main()