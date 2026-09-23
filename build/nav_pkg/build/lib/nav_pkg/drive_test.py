import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

from geometry_msgs.msg import TwistStamped


class DriveTest(Node):

    def __init__(self):
        super().__init__('drive_test')

        self.publisher_ = self.create_publisher(
            TwistStamped,
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
        msg = TwistStamped()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        # 직진
        msg.twist.linear.x = 0.2
        msg.twist.angular.z = 0.0

        self.publisher_.publish(msg)

        self.get_logger().info(
            f'linear.x={msg.twist.linear.x}, '
            f'angular.z={msg.twist.angular.z}'
        )

    def stop_robot(self):
        stop_msg = TwistStamped()

        stop_msg.header.stamp = self.get_clock().now().to_msg()
        stop_msg.header.frame_id = 'base_link'

        stop_msg.twist.linear.x = 0.0
        stop_msg.twist.angular.z = 0.0

        # 정지 명령을 여러 번 보내서 확실하게 전달
        for _ in range(5):
            stop_msg.header.stamp = self.get_clock().now().to_msg()
            self.publisher_.publish(stop_msg)

            rclpy.spin_once(
                self,
                timeout_sec=0.05
            )

        self.get_logger().info(
            'NILARM ROBOT STOPPED!'
        )


def main(args=None):

    # 중요:
    # ROS2가 Ctrl+C를 먼저 처리해서 context를 죽이지 않도록 함
    rclpy.init(
        args=args,
        signal_handler_options=SignalHandlerOptions.NO
    )

    node = DriveTest()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:

        # 아직 ROS context가 살아 있을 때 정지
        node.stop_robot()

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()