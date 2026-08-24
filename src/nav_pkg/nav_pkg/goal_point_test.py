import math
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions

from nav_msgs.msg import Odometry
from geometry_msgs.msg import TwistStamped


class GoalPointTest(Node):

    def __init__(self):

        super().__init__('goal_point_test')


        # =================================
        # 목표 좌표
        # 현재 위치(-1.71,-3.93) 기준 테스트
        # =================================

        self.goal_x = -1.0
        self.goal_y = -3.9


        # =================================
        # 속도
        # =================================

        self.linear_speed = 0.03

        self.angular_speed = 0.2


        # 도착 기준
        self.goal_tolerance = 0.10



        # =================================
        # 상태
        # =================================

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0


        self.finished = False
        self.stopping = False



        # =================================
        # ROS
        # =================================

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            qos_profile_sensor_data
        )


        self.cmd_pub = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )


        self.get_logger().info(
            "=========================="
        )

        self.get_logger().info(
            "GOAL POINT TEST START"
        )

        self.get_logger().info(
            f"TARGET X:{self.goal_x}"
            f" Y:{self.goal_y}"
        )

        self.get_logger().info(
            "=========================="
        )



    # =================================
    # Quaternion -> Yaw
    # =================================

    def quaternion_to_yaw(self,q):

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

    def odom_callback(self,msg):

        if self.finished or self.stopping:
            return



        self.x = (
            msg.pose.pose.position.x
        )

        self.y = (
            msg.pose.pose.position.y
        )


        self.yaw = (
            self.quaternion_to_yaw(
                msg.pose.pose.orientation
            )
        )



        # 목표까지 거리

        dx = (
            self.goal_x -
            self.x
        )

        dy = (
            self.goal_y -
            self.y
        )


        distance = math.sqrt(
            dx*dx +
            dy*dy
        )


        # 목표 방향

        target_yaw = math.atan2(
            dy,
            dx
        )


        # 방향 오차

        yaw_error = (
            target_yaw -
            self.yaw
        )


        # -pi ~ pi 변환

        yaw_error = math.atan2(
            math.sin(yaw_error),
            math.cos(yaw_error)
        )


        yaw_deg = math.degrees(
            yaw_error
        )



        self.get_logger().info(
            f"POS:"
            f"({self.x:.2f},"
            f"{self.y:.2f}) "
            f"DIST:{distance:.2f} "
            f"ANGLE:{yaw_deg:.1f}"
        )



        # =================================
        # 목표 도착
        # =================================

        if distance <= self.goal_tolerance:


            self.finished = True


            self.get_logger().info(
                "GOAL REACHED"
            )


            self.stop_robot()

            return



        cmd = self.make_cmd()



        # =================================
        # 방향 맞추기
        # =================================

        if abs(yaw_deg) > 10:


            # ★ 원래 방향

            if yaw_error > 0:

                # 왼쪽 회전

                cmd.twist.angular.z = (
                    self.angular_speed
                )


            else:

                # 오른쪽 회전

                cmd.twist.angular.z = (
                    -self.angular_speed
                )


            self.cmd_pub.publish(cmd)

            return



        # =================================
        # 직진
        # =================================

        cmd.twist.linear.x = (
            self.linear_speed
        )


        self.cmd_pub.publish(cmd)



    # =================================
    # TwistStamped
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
    # 확실한 정지
    # =================================

    def stop_robot(self):

        self.stopping = True


        self.get_logger().warn(
            "FINAL STOP"
        )


        for _ in range(50):

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



# =================================
# MAIN
# =================================

def main(args=None):


    rclpy.init(
        args=args,
        signal_handler_options=
        SignalHandlerOptions.NO
    )


    node = GoalPointTest()


    shutdown = False



    def handler(sig,frame):

        nonlocal shutdown


        shutdown = True


        node.stop_robot()



    signal.signal(
        signal.SIGINT,
        handler
    )



    try:

        while (
            rclpy.ok()
            and not shutdown
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

            node.stop_robot()



        node.destroy_node()



        if rclpy.ok():

            rclpy.shutdown()



if __name__ == "__main__":

    main()