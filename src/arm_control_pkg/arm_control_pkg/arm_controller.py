import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point
from geometry_msgs.msg import PoseStamped

from moveit.planning import MoveItPy


class ArmController(Node):

    def __init__(self):
        super().__init__('arm_controller')

        # -----------------------------
        # 1. 비전에서 과일 좌표 받기
        # -----------------------------
        self.subscription = self.create_subscription(
            Point,
            '/fruit_position',
            self.target_callback,
            10
        )

        # -----------------------------
        # 2. MoveIt 2 초기화
        # -----------------------------
        self.moveit = MoveItPy(
            node_name='moveit_py'
        )

        # MoveIt에 설정된 로봇팔 planning group
        self.arm = self.moveit.get_planning_component(
            'arm'
        )

        self.get_logger().info('Arm Controller Started')


    # ------------------------------------------------
    # 과일 좌표를 받으면 자동으로 실행되는 함수
    # ------------------------------------------------
    def target_callback(self, msg):

        x = msg.x
        y = msg.y
        z = msg.z

        self.get_logger().info(
            f'Fruit position: x={x:.2f}, y={y:.2f}, z={z:.2f}'
        )

        # 받은 좌표로 로봇팔 이동
        self.move_arm(x, y, z)


    # ------------------------------------------------
    # MoveIt 2를 이용해 로봇팔 이동
    # ------------------------------------------------
    def move_arm(self, x, y, z):

        # 1. 목표 Pose 생성
        target_pose = PoseStamped()

        # 기준 좌표계
        target_pose.header.frame_id = 'base_link'

        # 목표 위치
        target_pose.pose.position.x = x
        target_pose.pose.position.y = y
        target_pose.pose.position.z = z

        # 목표 방향
        target_pose.pose.orientation.x = 0.0
        target_pose.pose.orientation.y = 0.0
        target_pose.pose.orientation.z = 0.0
        target_pose.pose.orientation.w = 1.0

        self.get_logger().info('Target pose created')

        # 2. MoveIt에 목표 자세 전달
        self.arm.set_goal_state(
            pose_stamped_msg=target_pose,
            pose_link='end_effector_link'
        )

        # 3. 경로 계획
        plan_result = self.arm.plan()

        # 4. 경로가 생성되면 실행
        if plan_result:

            self.get_logger().info('Planning success')

            self.moveit.execute(
                plan_result.trajectory,
                controllers=[]
            )

        else:

            self.get_logger().warn('Planning failed')


def main(args=None):

    # ROS2 시작
    rclpy.init(args=args)

    # ArmController 노드 생성
    node = ArmController()

    # 계속 실행하면서 토픽 기다리기
    rclpy.spin(node)

    # 종료
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()