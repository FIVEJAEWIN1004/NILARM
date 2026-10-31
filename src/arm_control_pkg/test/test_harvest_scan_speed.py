"""Selective competition scan-speed tests."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_auto_scan_count_orange_harvest as scan,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


def test_scan_step_is_1_3x_faster_than_previous_scan_speed():
    transit_seconds = speed.transit_rotation_duration(30)
    step_seconds = speed.scan_step_rotation_duration(30)

    assert transit_seconds == pytest.approx(3.6)
    assert speed.SCAN_STEP_SPEED_MULTIPLIER == pytest.approx(2.704)
    assert step_seconds == pytest.approx(transit_seconds / 2.704)
    assert step_seconds == pytest.approx(1.331361, rel=1e-5)
    previous_scan_seconds = transit_seconds / 2.08
    assert previous_scan_seconds / step_seconds == pytest.approx(1.3)


@pytest.mark.parametrize(
    ("delta_deg", "expected"),
    [(30, 1.331361), (60, 2.662722), (90, 3.994083)],
)
def test_scan_step_keeps_2_704x_ratio(delta_deg, expected):
    transit_seconds = speed.transit_rotation_duration(delta_deg)
    step_seconds = speed.scan_step_rotation_duration(delta_deg)

    assert step_seconds == pytest.approx(transit_seconds / 2.704)
    assert step_seconds == pytest.approx(expected, rel=1e-5)
    assert speed.scan_target_rotation_duration(-110, delta_deg) == (
        pytest.approx(step_seconds))


def test_speed_configuration_separates_scan_from_other_rotations(monkeypatch):
    monkeypatch.setattr(scan.base, "CAMERA_MOVE_DURATION_SEC", 6.0)
    monkeypatch.setattr(scan.grasp, "HIGH_MOVE_DURATION_SEC", 12.0)
    monkeypatch.setattr(scan.grasp, "LOWER_MOVE_DURATION_SEC", 8.0)
    monkeypatch.setattr(scan.grasp, "LIFT_STEP_DURATION_SEC", 4.0)
    monkeypatch.setattr(scan.grasp, "RETURN_DURATION_SEC", 12.0)
    monkeypatch.setattr(scan.multi, "movement_duration", lambda _delta: 999.0)
    monkeypatch.setattr(scan, "scan_movement_duration", lambda _delta: 999.0)
    monkeypatch.setattr(scan, "park_arm", scan.park_arm)

    speed.configure_selective_speed()

    assert scan.base.CAMERA_MOVE_DURATION_SEC == pytest.approx(3.6)
    assert scan.multi.movement_duration is speed.transit_rotation_duration
    assert scan.scan_movement_duration is speed.scan_rotation_duration
    assert scan.park_arm is speed.park_at_target_speed


def test_omx_initialize_uses_dedicated_six_second_sequence(monkeypatch):
    events = []
    camera_joints = np.arange(5, dtype=float)

    class RecordingArm:
        def gripper(self, value, duration):
            events.append(("gripper", value, duration))

        def move_joints(self, joints, duration):
            events.append(("move", tuple(np.asarray(joints)), duration))

    monkeypatch.setattr(
        scan,
        "normalized_gripper_value",
        lambda _arm: events.append(("remember_gripper",)) or 0.35,
    )
    monkeypatch.setattr(
        scan.time,
        "sleep",
        lambda duration: events.append(("settle", duration)),
    )

    value = scan.initialize_arm_for_scan(RecordingArm(), camera_joints)

    assert value == pytest.approx(0.35)
    assert events == [
        (
            "gripper",
            scan.omx_robot.GRIPPER_READY,
            scan.INITIAL_GRIPPER_DURATION_SEC,
        ),
        (
            "move",
            tuple(np.asarray(scan.omx_robot.READY)),
            scan.INITIAL_READY_DURATION_SEC,
        ),
        ("remember_gripper",),
        (
            "move",
            tuple(camera_joints),
            scan.INITIAL_CAMERA_MOVE_DURATION_SEC,
        ),
        ("settle", scan.INITIAL_CAMERA_SETTLE_TIME_SEC),
    ]
    assert scan.INITIAL_GRIPPER_DURATION_SEC == pytest.approx(1.5)
    assert scan.INITIAL_READY_DURATION_SEC == pytest.approx(2.3)
    assert scan.INITIAL_CAMERA_MOVE_DURATION_SEC == pytest.approx(1.7)
    assert scan.INITIAL_CAMERA_SETTLE_TIME_SEC == pytest.approx(0.5)
    assert sum((
        scan.INITIAL_GRIPPER_DURATION_SEC,
        scan.INITIAL_READY_DURATION_SEC,
        scan.INITIAL_CAMERA_MOVE_DURATION_SEC,
        scan.INITIAL_CAMERA_SETTLE_TIME_SEC,
    )) == pytest.approx(6.0)


def test_scan_and_return_timings():
    assert scan.base.SETTLE_TIME_SEC == pytest.approx(1.0)
    assert speed.FIRST_SCAN_ENTRY_SPEED_MULTIPLIER == pytest.approx(2.0)
    first_entry = speed.scan_target_rotation_duration(-140, -140)
    assert first_entry == pytest.approx(3.106509, rel=1e-5)
    assert 4.038462 / first_entry == pytest.approx(1.3, rel=1e-5)


def test_post_scan_return_to_centre_caps_requested_2x_at_servo_limit():
    assert speed.SCAN_EXTRA_SPEED_MULTIPLIER == pytest.approx(2.08)
    assert speed.scan_rotation_duration(130) == pytest.approx(7.5)
    assert speed.POST_SCAN_RETURN_SPEEDUP == pytest.approx(2.0)
    duration = speed.post_scan_return_rotation_duration(130)
    assert duration == pytest.approx(
        130 * speed.v2.QUINTIC_PEAK_VELOCITY_FACTOR
        / speed.v2.SERVO_PROFILE_VELOCITY_DPS
    )
    assert duration == pytest.approx(5.916, abs=0.001)
    assert 130 / duration * 1.875 <= 41.2
    assert speed.scan_rotation_duration(30) == pytest.approx(1.730769, rel=1e-5)
