"""Manual departure gate timing tests without robot hardware."""

import numpy as np

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as poses,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as deposit,
)


class RecordingArm:
    def __init__(self, events):
        self.events = events
        self.kin = None

    def move_joints(self, joints, duration):
        self.events.append(("move", tuple(np.asarray(joints)), duration))

    def open_gripper(self, **_kwargs):
        self.events.append(("open",))

    def gripper(self, *_args, **_kwargs):
        self.events.append(("restore_gripper",))


def install_poses(monkeypatch):
    monkeypatch.setattr(poses, "_BIN_HOVER_JOINTS", np.full(5, 1.0))
    monkeypatch.setattr(poses, "_BIN_DROP_JOINTS", np.full(5, 2.0))
    monkeypatch.setattr(poses, "_BIN_FOLDED_JOINTS", np.full(5, 3.0))
    monkeypatch.setattr(deposit.time, "sleep", lambda _seconds: None)


def test_last_pumpkin_gate_is_after_hover_rise_before_arm_cleanup(monkeypatch):
    events = []
    install_poses(monkeypatch)
    monkeypatch.setattr(
        deposit,
        "departure_signal_gate",
        lambda: events.append(("departure_gate",)),
    )
    arm = RecordingArm(events)
    calibration = {"camera_joints": np.zeros(5)}

    deposit.deposit_open_then_rise(
        arm,
        calibration,
        default_gripper_value=0.3,
        is_last=True,
    )

    names = [event[0] for event in events]
    assert names[:5] == ["move", "move", "open", "move", "departure_gate"]
    assert names[5] == "restore_gripper"


def test_non_last_pumpkin_does_not_wait_for_departure(monkeypatch):
    events = []
    install_poses(monkeypatch)
    monkeypatch.setattr(
        deposit,
        "departure_signal_gate",
        lambda: events.append(("departure_gate",)),
    )
    arm = RecordingArm(events)

    deposit.deposit_open_then_rise(
        arm,
        {"camera_joints": np.zeros(5)},
        default_gripper_value=0.3,
        is_last=False,
    )

    assert "departure_gate" not in [event[0] for event in events]
