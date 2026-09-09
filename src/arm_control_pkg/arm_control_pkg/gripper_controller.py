import time


class GripperController:

    def __init__(self, arm_controller):
        self.arm_controller = arm_controller

    @property
    def arm(self):
        return self.arm_controller.arm

    def open(self):
        self.arm.open_gripper()
        time.sleep(0.8)

    def close(self):
        self.arm.close_gripper()
        time.sleep(1.2)