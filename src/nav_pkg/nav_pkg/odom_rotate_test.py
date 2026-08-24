import math
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions

from nav_msgs.msg import Odometry
from geometry_msgs.msg import TwistStamped


class OdomRotateTest(Node):

    def __init__(self):

        super().__init__('odom_rotate_test')


        # =====================================
        # 회전 설정
        # =====================================

        # 목표 회전 각도
        # 90도
        self.target_angle = 90.0

        # 회전 속도
        # rad/s
        self.angular_speed = 0.3


        # =====================================
        # 상태
        # =====================================

        self.start_yaw = None
        self.current_yaw = None

        self.finished = False
        self.stopping = False


        # =====================================
        # ODOM
        # =====================================

        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            qos_profile_sensor_data
        )


        # =====================================
        # CMD VEL
        # =====================================

        self.cmd_publisher = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )


        self.get_logger().info(
            '================================'
        )

        self.get_logger().info(
            'NILARM ODOM ROTATE TEST START'
        )

        self.get_logger().info(
            'Target : LEFT 90 degree'
        )

        self.get_logger().info(
            '================================'
        )


    # =====================================
    # Quaternion -> Yaw
    # =====================================

    def quaternion_to_yaw(self, q):

        siny = 2.0 * (
            q.w * q.z +
            q.x * q.y
        )

        cosy = 1.0 - 2.0 * (
            q.y*q.y +
            q.z*q.z
        )

        yaw = math.atan2(
            siny,
            cosy
        )

        return yaw



    # =====================================
    # ODOM CALLBACK
    # =====================================

    def odom_callback(self, msg):

        if self.finished or self.stopping:
            return


        # 현재 yaw 계산

        self.current_yaw = self.quaternion_to_yaw(
            msg.pose.pose.orientation
        )


        current_deg = math.degrees(
            self.current_yaw
        )


        # =================================
        # 시작 방향 저장
        # =================================

        if self.start_yaw is None:

            self.start_yaw = self.current_yaw


            self.get_logger().info(
                f'START YAW : '
                f'{current_deg:.1f} deg'
            )

            return



        # =================================
        # 회전량 계산
        # =================================

        delta_yaw = (
            self.current_yaw
            -
            self.start_yaw
        )


        # -pi ~ pi 보정

        delta_yaw = math.atan2(
            math.sin(delta_yaw),
            math.cos(delta_yaw)
        )


        delta_deg = math.degrees(
            delta_yaw
        )



        self.get_logger().info(
            f'ROTATE : '
            f'{delta_deg:.1f}/'
            f'{self.target_angle:.1f} deg'
        )



        # =================================
        # 목표 각도 도달
        # =================================

        if delta_deg >= self.target_angle:


            self.finished = True


            self.get_logger().info(
                'TARGET ANGLE REACHED'
            )


            self.emergency_stop()

            return



        # =================================
        # 아직 회전 필요
        # =================================

        cmd = self.make_cmd()


        # 왼쪽 회전

        cmd.twist.angular.z = (
            self.angular_speed
        )


        self.cmd_publisher.publish(
            cmd
        )



    # =====================================
    # TwistStamped 생성
    # =====================================

    def make_cmd(self):

        cmd = TwistStamped()

        cmd.header.stamp = (
            self.get_clock()
            .now()
            .to_msg()
        )

        cmd.header.frame_id = (
            'base_link'
        )


        return cmd



    # =====================================
    # 안전 정지
    # =====================================

    def emergency_stop(self):

        if self.stopping:
            return


        self.stopping = True


        self.get_logger().warn(
            'EMERGENCY STOP'
        )


        for _ in range(40):

            if not rclpy.ok():
                break


            stop = self.make_cmd()

            stop.twist.linear.x = 0.0
            stop.twist.angular.z = 0.0


            self.cmd_publisher.publish(
                stop
            )


            time.sleep(0.05)



        self.get_logger().warn(
            'ROBOT STOPPED'
        )



# =====================================
# MAIN
# =====================================

def main(args=None):


    rclpy.init(
        args=args,
        signal_handler_options=
        SignalHandlerOptions.NO
    )


    node = OdomRotateTest()


    shutdown_requested = False



    def signal_handler(sig, frame):

        nonlocal shutdown_requested


        if shutdown_requested:
            return


        shutdown_requested = True


        print(
            '\nCTRL+C detected!'
        )


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