#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class CmdVelBridge(Node):

    def __init__(self):
        super().__init__('cmd_vel_bridge')

        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info(
            'NILARM CMD VEL BRIDGE STARTED'
        )

    def cmd_vel_callback(self, msg):

        linear_x = msg.linear.x
        angular_z = msg.angular.z

        self.get_logger().info(
            f'RECEIVED /cmd_vel | '
            f'linear.x={linear_x:.3f} | '
            f'angular.z={angular_z:.3f}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = CmdVelBridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()