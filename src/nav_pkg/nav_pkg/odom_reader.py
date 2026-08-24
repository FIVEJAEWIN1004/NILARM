import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class OdomReader(Node):

    def __init__(self):
        super().__init__('odom_reader')

        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.get_logger().info(
            'NILARM odom reader started!'
        )

    def odom_callback(self, msg):

        # =========================
        # 현재 위치
        # =========================

        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        # =========================
        # 현재 방향
        # Quaternion
        # =========================

        qx = msg.pose.pose.orientation.x
        qy = msg.pose.pose.orientation.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w

        # Quaternion → Yaw 변환
        yaw = math.atan2(
            2.0 * (qw * qz + qx * qy),
            1.0 - 2.0 * (qy * qy + qz * qz)
        )

        # rad → degree
        yaw_deg = math.degrees(yaw)

        self.get_logger().info(
            f'X: {x:.3f} m | '
            f'Y: {y:.3f} m | '
            f'YAW: {yaw_deg:.1f} deg'
        )


def main(args=None):

    rclpy.init(args=args)

    node = OdomReader()

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