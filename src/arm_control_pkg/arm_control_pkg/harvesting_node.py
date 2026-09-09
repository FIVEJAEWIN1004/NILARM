import rclpy
from rclpy.node import Node

from arm_control_pkg.arm_controller import (
    ArmController
)
from arm_control_pkg.gripper_controller import (
    GripperController
)
from arm_control_pkg.target_receiver import (
    TargetReceiver
)


class HarvestingNode(Node):

    def __init__(self):
        super().__init__("harvesting_node")

        self.arm_controller = ArmController()

        self.gripper_controller = (
            GripperController(
                self.arm_controller
            )
        )

        self.target_receiver = (
            TargetReceiver(self)
        )

        self.place_position = (
            0.18,
            0.12,
            0.08
        )

        self.started = False

        self.timer = self.create_timer(
            0.5,
            self.control_loop
        )

    def control_loop(self):
        if self.started:
            return

        ripe_targets = [
            target
            for target
            in self.target_receiver.targets
            if target["ripe"]
        ]

        if not ripe_targets:
            return

        self.started = True

        try:
            self.harvest_all(
                ripe_targets
            )

        except Exception as error:
            self.get_logger().error(
                f"수확 오류: {error}"
            )

        finally:
            self.started = False

    def harvest_all(self, targets):
        for target in targets:
            self.pick(
                target["position"]
            )

            self.place(
                self.place_position
            )

    def pick(self, position):
        arm = self.arm_controller
        gripper = self.gripper_controller

        gripper.open()
        arm.move_above(position)
        arm.move_down(position)
        gripper.close()
        arm.move_up(position)

    def place(self, position):
        arm = self.arm_controller
        gripper = self.gripper_controller

        arm.move_above(position)
        arm.move_down(position)
        gripper.open()
        arm.move_up(position)


def main(args=None):
    rclpy.init(args=args)

    node = HarvestingNode()

    try:
        node.arm_controller.connect()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.arm_controller.disconnect()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()