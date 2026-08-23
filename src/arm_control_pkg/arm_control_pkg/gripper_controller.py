import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class GripperController(Node):

    def __init__(self):
        super().__init__('gripper_controller')

        self.subscription = self.create_subscription(
            Bool,
            '/gripper_command',
            self.gripper_callback,
            10
        )

        self.get_logger().info('Gripper Controller Started')

    def gripper_callback(self, msg):

        if msg.data:
            self.close_gripper()
        else:
            self.open_gripper()

    def close_gripper(self):
        self.get_logger().info('Gripper CLOSE')

        # 실제 모터 제어 코드

    def open_gripper(self):
        self.get_logger().info('Gripper OPEN')

        # 실제 모터 제어 코드


def main(args=None):
    rclpy.init(args=args)

    node = GripperController()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()