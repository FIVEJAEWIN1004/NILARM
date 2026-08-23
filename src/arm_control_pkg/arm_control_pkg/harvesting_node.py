import rclpy
from rclpy.node import Node


class HarvestingNode(Node):

    def __init__(self):
        super().__init__('harvesting_node')

        self.get_logger().info('Harvesting System Started')

    def harvest(self, x, y, z):

        self.move_to_target(x, y, z)

        self.close_gripper()

        self.move_to_storage()

        self.open_gripper()

        self.move_home()

    def move_to_target(self, x, y, z):
        self.get_logger().info(
            f'Move to fruit: {x}, {y}, {z}'
        )

    def close_gripper(self):
        self.get_logger().info('Grab fruit')

    def move_to_storage(self):
        self.get_logger().info('Move to storage')

    def open_gripper(self):
        self.get_logger().info('Release fruit')

    def move_home(self):
        self.get_logger().info('Return home')


def main(args=None):
    rclpy.init(args=args)

    node = HarvestingNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()