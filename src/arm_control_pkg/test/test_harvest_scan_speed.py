"""Selective competition scan-speed tests."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_auto_scan_count_orange_harvest as scan,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


def trapezoid_points(delta_deg, hz=100.0):
    q1 = np.radians([delta_deg, 0.0, 0.0, 0.0, 0.0])
    return list(speed.joint_trajectory.trapezoid_path(
        np.zeros(5), q1, speed.SCAN_TRAPEZOID_SPEED_DPS,
        speed.SCAN_TRAPEZOID_ACCEL_DPS2, hz)), q1


@pytest.mark.parametrize(
    ("delta_deg", "seconds"),
    # old quintic: 1.33 s / 5.33 s; the first -140 deg entry ~4.0 s (servo-capped)
    [(30, 0.97), (-120, 3.28), (-140, 3.79), (3, 0.25)],
)
def test_scan_view_trapezoid_time_limits_and_exact_end(delta_deg, seconds):
    points, q1 = trapezoid_points(delta_deg)
    path = np.degrees(np.asarray([np.zeros(5)] + points))
    velocity = np.diff(path, axis=0) * 100.0
    acceleration = np.diff(velocity, axis=0) * 100.0

    assert len(points) / 100.0 == pytest.approx(seconds, abs=0.011)
    np.testing.assert_array_equal(points[-1], q1)
    assert np.max(np.abs(velocity)) <= speed.SCAN_TRAPEZOID_SPEED_DPS + 1e-6
    # discrete 100 Hz differencing smears the ramp corners by one sample
    assert np.max(np.abs(acceleration)) <= speed.SCAN_TRAPEZOID_ACCEL_DPS2 * 1.01
    assert np.all(np.diff(path[:, 0]) * np.sign(delta_deg) >= -1e-9)  # monotonic


def test_scan_trapezoid_stays_inside_servo_profile():
    assert speed.SCAN_TRAPEZOID_SPEED_DPS < speed.v2.SERVO_PROFILE_VELOCITY_DPS
    assert speed.SCAN_TRAPEZOID_ACCEL_DPS2 < speed.v2.SERVO_PROFILE_ACCELERATION_DPS2
    with pytest.raises(ValueError):
        speed.joint_trajectory.move_joints_trapezoid(
            object(), np.zeros(5), 50.0, 200.0)


def test_scan_views_use_trapezoid_hook(monkeypatch):
    calls = []
    monkeypatch.setattr(scan, "move_to_scan_view", scan.move_to_scan_view)
    monkeypatch.setattr(speed.joint_trajectory, "move_joints_trapezoid",
                        lambda *args: calls.append(args))
    speed.configure_selective_speed()
    scan.move_to_scan_view("arm", "joints", 70.0, 120.0)
    assert calls == [("arm", "joints", 39.0, 200.0)]


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
