import math
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions

from nav_msgs.msg import Odometry
from geometry_msgs.msg import TwistStamped


class PathTest(Node):

    def __init__(self):

        super().__init__('path_test')


        # =================================
        # 목표 설정
        # =================================

        # ★ 직진 거리 30cm
        self.move_distance = 0.30

        # 회전 각도
        self.rotate_angle = 90.0


        # 속도

        self.linear_speed = 0.02

        self.angular_speed = 0.3



        # =================================
        # 상태 머신
        # =================================

        # MOVE:
        # 직진

        # ROTATE:
        # 회전

        self.state = "MOVE"


        # 몇 번째 변인지

        self.count = 0

        self.max_count = 4



        # =================================
        # 위치 저장
        # =================================

        self.start_x = None
        self.start_y = None

        self.start_yaw = None


        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0


        self.finished = False
        self.stopping = False



        # =================================
        # Subscriber
        # =================================

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            qos_profile_sensor_data
        )


        # =================================
        # Publisher
        # =================================

        self.cmd_pub = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )


        self.get_logger().info(
            "=============================="
        )

        self.get_logger().info(
            "NILARM PATH TEST START"
        )

        self.get_logger().info(
            "MOVE : 0.30m"
        )

        self.get_logger().info(
            "ROTATE : 90deg"
        )

        self.get_logger().info(
            "=============================="
        )



    # =================================
    # Quaternion -> Yaw
    # =================================

    def quaternion_to_yaw(self, q):

        siny = 2.0 * (
            q.w*q.z +
            q.x*q.y
        )

        cosy = 1.0 - 2.0 * (
            q.y*q.y +
            q.z*q.z
        )

        return math.atan2(
            siny,
            cosy
        )



    # =================================
    # ODOM CALLBACK
    # =================================

    def odom_callback(self, msg):

        if self.finished or self.stopping:
            return



        self.current_x = (
            msg.pose.pose.position.x
        )

        self.current_y = (
            msg.pose.pose.position.y
        )


        self.current_yaw = (
            self.quaternion_to_yaw(
                msg.pose.pose.orientation
            )
        )



        # 첫 위치 저장

        if self.start_x is None:


            self.start_x = self.current_x
            self.start_y = self.current_y
            self.start_yaw = self.current_yaw


            self.get_logger().info(
                "START POSITION SAVED"
            )


            return



        # =============================
        # 직진 상태
        # =============================

        if self.state == "MOVE":

            self.move()



        # =============================
        # 회전 상태
        # =============================

        elif self.state == "ROTATE":

            self.rotate()



    # =================================
    # 직진
    # =================================

    def move(self):


        dx = (
            self.current_x -
            self.start_x
        )


        dy = (
            self.current_y -
            self.start_y
        )


        distance = math.sqrt(
            dx*dx +
            dy*dy
        )


        self.get_logger().info(
            f"MOVE "
            f"{distance:.3f}/"
            f"{self.move_distance:.3f}m"
        )



        # 30cm 도착

        if distance >= self.move_distance:


            self.stop_once()


            self.start_yaw = (
                self.current_yaw
            )


            self.state = "ROTATE"



            self.get_logger().info(
                "MOVE COMPLETE"
            )


            return



        # 직진

        cmd = self.make_cmd()

        cmd.twist.linear.x = (
            self.linear_speed
        )


        self.cmd_pub.publish(cmd)



    # =================================
    # 회전
    # =================================

    def rotate(self):


        delta = (
            self.current_yaw -
            self.start_yaw
        )


        # -pi ~ pi 보정

        delta = math.atan2(
            math.sin(delta),
            math.cos(delta)
        )


        degree = math.degrees(delta)



        self.get_logger().info(
            f"ROTATE "
            f"{degree:.1f}/"
            f"{self.rotate_angle}deg"
        )



        # 90도 완료

        if degree >= self.rotate_angle:


            self.stop_once()


            self.count += 1



            # 4번 완료

            if self.count >= self.max_count:


                self.finished = True


                self.get_logger().info(
                    "PATH COMPLETE"
                )


                self.emergency_stop()


                return



            # 다음 직진 준비

            self.start_x = (
                self.current_x
            )

            self.start_y = (
                self.current_y
            )


            self.state = "MOVE"


            self.get_logger().info(
                "NEXT MOVE"
            )


            return



        # 왼쪽 회전

        cmd = self.make_cmd()


        cmd.twist.angular.z = (
            self.angular_speed
        )


        self.cmd_pub.publish(cmd)



    # =================================
    # TwistStamped 생성
    # =================================

    def make_cmd(self):

        cmd = TwistStamped()


        cmd.header.stamp = (
            self.get_clock()
            .now()
            .to_msg()
        )


        cmd.header.frame_id = (
            "base_link"
        )


        return cmd



    # =================================
    # 순간 정지
    # =================================

    def stop_once(self):

        stop = self.make_cmd()

        stop.twist.linear.x = 0.0
        stop.twist.angular.z = 0.0


        self.cmd_pub.publish(stop)


        time.sleep(0.2)



    # =================================
    # 안전 정지
    # =================================

    def emergency_stop(self):

        if self.stopping:
            return


        self.stopping = True


        self.get_logger().warn(
            "EMERGENCY STOP"
        )


        for _ in range(40):

            if not rclpy.ok():
                break


            stop = self.make_cmd()

            stop.twist.linear.x = 0.0
            stop.twist.angular.z = 0.0


            self.cmd_pub.publish(stop)


            time.sleep(0.05)



        self.get_logger().warn(
            "ROBOT STOPPED"
        )





def main(args=None):


    rclpy.init(
        args=args,
        signal_handler_options=
        SignalHandlerOptions.NO
    )


    node = PathTest()


    shutdown_requested = False



    def signal_handler(sig, frame):

        nonlocal shutdown_requested


        if shutdown_requested:
            return


        shutdown_requested = True


        print(
            "\nCTRL+C detected!"
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



if __name__ == "__main__":

    main()