"""Held-pumpkin transport speed tests without connecting to hardware."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as transport,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


class RecordingArm:
    def __init__(self):
        self.moves = []

    def move_joints(self, joints, duration):
        self.moves.append((np.asarray(joints, dtype=float), float(duration)))


def test_held_transport_duration_is_twice_current_speed():
    assert transport.HELD_TRANSPORT_SPEED_MULTIPLIER == pytest.approx(2.0)
    assert transport.held_transport_duration(4.8) == pytest.approx(2.4)
    assert speed.BIN_HOVER_DURATION_SEC == pytest.approx(2.4)


def test_lift_fold_and_bin_rotation_are_all_twice_as_fast(monkeypatch):
    arm = RecordingArm()
    stages = [np.full(5, index, dtype=float) for index in range(4)]
    prealign = np.zeros(5, dtype=float)
    folded = np.ones(5, dtype=float)

    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    monkeypatch.setattr(transport.scan.grasp, "LIFT_STEP_DURATION_SEC", 3.0)
    monkeypatch.setattr(transport.scan.grasp, "RETURN_DURATION_SEC", 6.0)
    monkeypatch.setattr(
        transport.scan.grasp,
        "APPROACH_CLEARANCES_M",
        (0.080, 0.030, 0.010, 0.000),
    )
    monkeypatch.setattr(
        transport.scan.multi,
        "movement_duration",
        lambda _rotation_deg: 8.0,
    )

    transport.move_held_pumpkin_to_bin(arm, prealign, stages)

    assert [duration for _joints, duration in arm.moves] == pytest.approx(
        [1.5, 1.5, 1.5, 3.0, 4.0]
    )
