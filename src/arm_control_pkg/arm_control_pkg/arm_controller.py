import math
import time

from omx_f import OmxFollower


class ArmController:

    def __init__(self):
        self.arm = None
        self.pitch = math.radians(90)
        self.hover = 0.05

    def connect(self):
        self.arm = OmxFollower().connect()
        self.arm.ready(duration=5.0)

    def move_to_scan_pose(
        self,
        joints,
        duration=2.5
    ):
        self.arm.move_joints(
            joints,
            duration=duration
        )

    def move_above(self, position):
        x, y, z = position

        self.arm.movej(
            x,
            y,
            z + self.hover,
            pitch=self.pitch,
            duration=3.0
        )

    def move_down(self, position):
        x, y, z = position

        self.arm.movel(
            x,
            y,
            z,
            pitch=self.pitch,
            speed=20
        )

    def move_up(self, position):
        x, y, z = position

        self.arm.movel(
            x,
            y,
            z + self.hover,
            pitch=self.pitch,
            speed=40
        )

    def ready(self):
        self.arm.ready(duration=3.0)

    def park(self):
        self.arm.park()

    def disconnect(self):
        if self.arm is not None:
            self.arm.park()
            self.arm.disconnect()
            self.arm = None