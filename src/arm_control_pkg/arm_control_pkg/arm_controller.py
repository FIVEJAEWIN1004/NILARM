import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point


class ArmController(Node):

    def __init__(self):
        super().__init__('arm_controller')

        self.subscription = self.create_subscription(
            Point,
            '/fruit_position',
            self.target_callback,
            10
        )

        self.get_logger().info('Arm Controller Started')

    def target_callback(self, msg):
        x = msg.x
        y = msg.y
        z = msg.z

        self.get_logger().info(
            f'Fruit position: x={x:.2f}, y={y:.2f}, z={z:.2f}'
        )

        self.move_arm(x, y, z)

    def move_arm(self, x, y, z):
        # 나중에 MoveIt / 역기구학 코드 연결
        self.get_logger().info(
            f'Moving arm to ({x}, {y}, {z})'
        )


def main(args=None):
    rclpy.init(args=args)

    node = ArmController()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()