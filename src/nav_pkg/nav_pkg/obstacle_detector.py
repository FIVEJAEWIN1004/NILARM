import math
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped


class ObstacleDetector(Node):

    def __init__(self):
        super().__init__('obstacle_detector')

        # ==========================================
        # 주행 설정
        # ==========================================

        # 40cm 이내 장애물 → 회피 시작
        self.stop_distance = 0.40

        # 회피 후 정면 60cm 확보 → 다시 직진
        self.clear_distance = 0.60

        # 정상 직진 속도
        self.linear_speed = 0.02

        # 회피 중 전진 속도
        self.avoid_linear_speed = 0.01

        # 회전 속도
        self.angular_speed = 0.15

        # ==========================================
        # 상태
        # ==========================================

        self.state = 'NORMAL'
        self.turn_direction = None

        # 마지막 LiDAR 수신 시간
        self.last_scan_time = time.monotonic()

        # 종료 중인지 확인
        self.stopping = False

        # ==========================================
        # LiDAR Subscriber
        # ==========================================

        self.scan_subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )

        # ==========================================
        # cmd_vel Publisher
        # ==========================================

        self.cmd_publisher = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )

        # ==========================================
        # Watchdog
        #
        # 0.1초마다 LiDAR가 살아있는지 확인
        # ==========================================

        self.watchdog_timer = self.create_timer(
            0.1,
            self.watchdog_callback
        )

        self.get_logger().info(
            'NILARM SAFE obstacle avoidance STARTED'
        )

    # ==============================================
    # LiDAR callback
    # ==============================================

    def scan_callback(self, msg):

        if self.stopping:
            return

        # LiDAR가 정상적으로 들어왔다는 시간 기록
        self.last_scan_time = time.monotonic()

        ranges = msg.ranges

        # 정면 ±30도
        front_indices = (
            list(range(0, 31))
            + list(range(330, 360))
        )

        # 앞-왼쪽
        front_left_indices = range(30, 91)

        # 앞-오른쪽
        front_right_indices = range(270, 331)

        # 왼쪽
        left_indices = range(60, 121)

        # 오른쪽
        right_indices = range(240, 301)

        # ==========================================
        # 거리 계산
        # ==========================================

        front = self.get_distance(
            ranges,
            front_indices
        )

        front_left = self.get_distance(
            ranges,
            front_left_indices
        )

        front_right = self.get_distance(
            ranges,
            front_right_indices
        )

        left = self.get_distance(
            ranges,
            left_indices
        )

        right = self.get_distance(
            ranges,
            right_indices
        )

        # ==========================================
        # NORMAL 상태
        # ==========================================

        if self.state == 'NORMAL':

            if front <= self.stop_distance:

                self.state = 'AVOIDING'

                left_space = min(
                    front_left,
                    left
                )

                right_space = min(
                    front_right,
                    right
                )

                if left_space >= right_space:
                    self.turn_direction = 'LEFT'

                else:
                    self.turn_direction = 'RIGHT'

                self.get_logger().warn(
                    f'OBSTACLE {front:.2f}m '
                    f'-> {self.turn_direction}'
                )

        # ==========================================
        # AVOIDING 상태
        # ==========================================

        elif self.state == 'AVOIDING':

            if front >= self.clear_distance:

                self.state = 'NORMAL'
                self.turn_direction = None

                self.get_logger().info(
                    'PATH CLEAR -> NORMAL'
                )

        # ==========================================
        # 주행 명령
        # ==========================================

        cmd = self.make_cmd()

        if self.state == 'NORMAL':

            cmd.twist.linear.x = (
                self.linear_speed
            )

            cmd.twist.angular.z = 0.0

            decision = 'GO STRAIGHT'

        elif self.state == 'AVOIDING':

            cmd.twist.linear.x = (
                self.avoid_linear_speed
            )

            if self.turn_direction == 'LEFT':

                cmd.twist.angular.z = (
                    self.angular_speed
                )

                decision = 'CURVE LEFT'

            elif self.turn_direction == 'RIGHT':

                cmd.twist.angular.z = (
                    -self.angular_speed
                )

                decision = 'CURVE RIGHT'

            else:

                cmd.twist.linear.x = 0.0
                cmd.twist.angular.z = 0.0

                decision = 'STOP'

        self.cmd_publisher.publish(cmd)

        self.get_logger().info(
            f'FRONT:{front:.2f} | '
            f'FL:{front_left:.2f} | '
            f'FR:{front_right:.2f} | '
            f'L:{left:.2f} | '
            f'R:{right:.2f} | '
            f'{decision}'
        )

    # ==============================================
    # LiDAR Watchdog
    # ==============================================

    def watchdog_callback(self):

        if self.stopping:
            return

        elapsed = (
            time.monotonic()
            - self.last_scan_time
        )

        # LiDAR 데이터가 0.5초 이상 안 들어오면
        # 무조건 정지
        if elapsed > 0.5:

            stop_msg = self.make_cmd()

            stop_msg.twist.linear.x = 0.0
            stop_msg.twist.angular.z = 0.0

            self.cmd_publisher.publish(
                stop_msg
            )

            self.get_logger().error(
                'LiDAR TIMEOUT -> STOP'
            )

    # ==============================================
    # cmd_vel 메시지 생성
    # ==============================================

    def make_cmd(self):

        cmd = TwistStamped()

        cmd.header.stamp = (
            self.get_clock().now().to_msg()
        )

        cmd.header.frame_id = 'base_link'

        cmd.twist.linear.x = 0.0
        cmd.twist.linear.y = 0.0
        cmd.twist.linear.z = 0.0

        cmd.twist.angular.x = 0.0
        cmd.twist.angular.y = 0.0
        cmd.twist.angular.z = 0.0

        return cmd

    # ==============================================
    # 거리 계산
    # ==============================================

    def get_distance(
        self,
        ranges,
        indices
    ):

        valid_ranges = []

        for i in indices:

            if i >= len(ranges):
                continue

            distance = ranges[i]

            if (
                math.isfinite(distance)
                and distance >= 0.12
                and distance <= 3.5
            ):
                valid_ranges.append(
                    distance
                )

        if not valid_ranges:
            return 3.5

        return min(valid_ranges)

    # ==============================================
    # ★ 안전 정지
    # ==============================================

    def emergency_stop(self):

        if self.stopping:
            return

        self.stopping = True

        self.get_logger().warn(
            '=============================='
        )

        self.get_logger().warn(
            'EMERGENCY STOP'
        )

        self.get_logger().warn(
            'Sending ZERO velocity...'
        )

        # 약 2초 동안
        # 0속도 명령을 계속 발행
        #
        # 사용자가 직접 확인한
        # ros2 topic pub -r 10 방식과 비슷하게
        # 반복해서 ZERO를 보냄

        for _ in range(40):

            if not rclpy.ok():
                break

            stop_msg = self.make_cmd()

            self.cmd_publisher.publish(
                stop_msg
            )

            # DDS가 실제 메시지를 보낼 시간 확보
            rclpy.spin_once(
                self,
                timeout_sec=0.01
            )

            time.sleep(0.04)

        self.get_logger().warn(
            'ZERO velocity sent.'
        )

        self.get_logger().warn(
            '=============================='
        )


# ==================================================
# main
# ==================================================

def main(args=None):

    # ==============================================
    # 중요:
    # rclpy가 SIGINT를 먼저 처리하지 않도록 설정
    # ==============================================

    rclpy.init(
        args=args,
        signal_handler_options=rclpy.signals.SignalHandlerOptions.NO
    )

    node = ObstacleDetector()

    shutdown_requested = False

    # ==============================================
    # Ctrl+C 직접 처리
    # ==============================================

    def signal_handler(sig, frame):

        nonlocal shutdown_requested

        if shutdown_requested:
            return

        shutdown_requested = True

        print('\nCTRL+C detected!')

        # ROS가 살아있는 상태에서
        # 먼저 ZERO 속도 전송
        node.emergency_stop()

    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    try:

        # rclpy.spin() 대신 직접 반복
        while (
            rclpy.ok()
            and not shutdown_requested
        ):

            rclpy.spin_once(
                node,
                timeout_sec=0.1
            )

    finally:

        # 어떤 이유로 루프가 끝나도
        # 마지막으로 정지 시도
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