import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class DriveTest(Node):

    def __init__(self):
        super().__init__('drive_test')

        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10  
        )

        self.timer = self.create_timer(
            0.5,
            self.timer_callback
        )

        self.get_logger().info( 
            'NILARM drive test node started!'
        )

    def timer_callback(self):
        msg = Twist()

        msg.linear.x = 0.2
        msg.angular.z = 0.0

        self.publisher.publish(msg)

        self.get_logger().info(
            f'linear.x={msg.linear.x}, angular.z={msg.angular.z}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = DriveTest()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()