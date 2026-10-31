"""Held-pumpkin lift/transport/bin timing tests without hardware."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as transport,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)

SPEED = 21.9
SERVO_PROFILE_VELOCITY_DPS = 30 * 0.229 * 6.0  # 41.2 deg/s
SERVO_PROFILE_ACCEL_DPS2 = 215.0
HZ = 100.0


@pytest.fixture(autouse=True)
def no_stream_sleep(monkeypatch):
    speed.reset_direct_hover_state()
    monkeypatch.setattr(
        transport.joint_trajectory, "stream",
        lambda path, write, _hz: [write(point) for point in path] and 0)
    yield
    speed.reset_direct_hover_state()


class RecordingArm:
    hz = HZ

    def __init__(self, start=None):
        self.moves = []
        self.events = []
        self.streamed = []
        self.grippers = []
        self.gripper_calls = []
        self.parks = []
        self.kin = None
        self.start = start

    def joints(self):
        return self.start

    def check_limits(self, q, _current=None):
        return np.asarray(q, dtype=float)

    def _write(self, q):
        self.streamed.append(np.asarray(q, dtype=float))

    def move_joints(self, joints, duration):
        self.moves.append((np.asarray(joints, dtype=float), float(duration)))
        self.events.append("move")

    def open_gripper(self, **_kwargs):
        self.events.append("open")

    def gripper(self, value, duration, **_kwargs):
        self.grippers.append((value, duration))
        self.gripper_calls.append((value, duration, _kwargs))
        self.events.append(
            "release_gripper"
            if _kwargs.get("stall_guard")
            else "restore_gripper"
        )

    def park(self, duration):
        self.parks.append(duration)


def deg_joints(*values):
    return np.radians(np.asarray(values, dtype=float))


def peak_dps(start, target, duration):
    delta = np.max(np.abs(np.degrees(np.asarray(target) - np.asarray(start))))
    return delta / duration * 1.875


def test_common_target_speed_stays_under_servo_limit():
    assert transport.TARGET_AVERAGE_JOINT_SPEED_DPS == pytest.approx(SPEED)
    assert SPEED * 1.875 == pytest.approx(41.0625)
    assert SPEED * 1.875 <= SERVO_PROFILE_VELOCITY_DPS
    # Largest joint decides; the floor wins for short moves.
    start = deg_joints(0, 0, 0, 0, 0)
    assert transport.duration_for_target_joint_speed(
        start, deg_joints(10, -43.8, 5, 0, 0), min_duration=1.0
    ) == pytest.approx(2.0)
    assert transport.duration_for_target_joint_speed(
        start, deg_joints(1, 0, 0, 0, 0), min_duration=1.0
    ) == pytest.approx(1.0)


def streamed_speed_dps(points, k):
    return np.degrees(points[k + 1] - points[k - 1]) * HZ / 2.0


def test_lift_streams_through_waypoints_then_folds_and_rotates(monkeypatch):
    # Signed joint changes from the real IK at azimuth -130 deg.
    grasp = deg_joints(-126.4, 10, 20, 30, 0)
    plus10 = grasp + deg_joints(0, -3.4, -0.6, 4.0, 0)
    plus30 = plus10 + deg_joints(0, -5.8, -2.1, 7.9, 0)
    plus80 = plus30 + deg_joints(0, -8.5, -10.5, 19.0, 0)
    stages = [plus80, plus30, plus10, grasp]
    prealign = plus80 + deg_joints(0, -26.0, -4.4, -2.8, -14.4)
    folded = prealign.copy()
    folded[0] = np.radians(-23.55)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    arm = RecordingArm(grasp)
    captured_segments = []
    original_continuous_move = (
        transport.joint_trajectory.move_joints_continuous
    )

    def capture_continuous_move(arm_arg, segments, via_speed_caps_dps):
        captured_segments.extend(segments)
        return original_continuous_move(
            arm_arg, segments, via_speed_caps_dps
        )

    monkeypatch.setattr(
        transport.joint_trajectory,
        "move_joints_continuous",
        capture_continuous_move,
    )

    transport.move_held_pumpkin_to_bin(arm, prealign, stages)

    # Only the first two ⑮ segments use the early-lift speedup.  The third
    # lift and ⑯a keep their existing dynamic calculations.
    fold_s = transport.duration_with_safe_speedup(
        plus80,
        prealign,
        min_duration=transport.HELD_FOLD_MIN_DURATION_SEC,
        speedup=transport.HELD_BIN_MOVE_SPEEDUP,
    )
    lift_durations = [duration for _target, duration in captured_segments[:3]]
    knots = np.cumsum([
        int(np.ceil(duration * HZ))
        for duration in (*lift_durations, fold_s)
    ]) - 1
    points = arm.streamed
    assert len(points) == knots[-1] + 1
    for k, waypoint in zip(knots, [plus10, plus30, plus80, prealign]):
        np.testing.assert_array_equal(points[k], waypoint)  # exact, in order

    # +10/+30 mm: lifting joints keep moving (no stop); j1/j5 stay still.
    for k in knots[:2]:
        speed_dps = streamed_speed_dps(points, k)
        assert np.all(np.abs(speed_dps[1:4]) > 0.3)
        assert np.all(np.abs(speed_dps[[0, 4]]) < 0.05)
    # +80 mm: j2/j3 continue into the fold at <= 5 deg/s; j4 reverses -> 0.
    speed_dps = streamed_speed_dps(points, knots[2])
    assert np.all(np.abs(speed_dps[1:3]) > 0.3)
    assert np.all(np.abs(speed_dps[1:3]) <= 5.0 + 0.05)
    assert np.all(np.abs(speed_dps[[0, 3, 4]]) < 0.05)
    # Ends at rest on the fold pose.
    assert np.max(np.abs(np.degrees(points[-1] - points[-2]))) * HZ < 0.05

    path = np.degrees(np.asarray([grasp] + points))
    velocity = np.diff(path, axis=0) * HZ
    accel = np.diff(velocity, axis=0) * HZ
    assert np.max(np.abs(velocity)) <= SERVO_PROFILE_VELOCITY_DPS
    assert np.max(np.abs(accel)) <= SERVO_PROFILE_ACCEL_DPS2

    assert lift_durations[:2] == pytest.approx([0.50, 0.50])
    assert lift_durations[2] == pytest.approx(0.87, abs=0.01)
    assert sum(lift_durations) == pytest.approx(1.87, abs=0.01)
    assert 2.47 - sum(lift_durations) == pytest.approx(0.60, abs=0.01)

    # ⑯b stays a separate rest-to-rest move after the fold is complete.
    assert len(arm.moves) == 1
    np.testing.assert_allclose(arm.moves[0][0], folded)
    assert arm.moves[0][1] == pytest.approx(
        102.85 * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS)


def test_held_floors():
    assert transport.LIFT_STEP_MIN_DURATION_SEC == pytest.approx(0.8)
    assert transport.LIFT_EARLY_SPEEDUP == pytest.approx(1.7)
    assert transport.LIFT_EARLY_MIN_DURATION_SEC == pytest.approx(0.5)
    assert transport.HELD_FOLD_MIN_DURATION_SEC == pytest.approx(1.4)
    assert transport.HELD_BIN_ROTATION_MIN_DURATION_SEC == pytest.approx(1.5)
    assert speed.BIN_HOVER_MIN_DURATION_SEC == pytest.approx(1.5)
    assert speed.BIN_DESCENT_MIN_DURATION_SEC == pytest.approx(2.0)
    assert speed.OPEN_GRIPPER_RISE_MIN_DURATION_SEC == pytest.approx(1.9)


def test_early_lift_uses_longer_duration_for_large_joint_change():
    start = deg_joints(0, 0, 0, 0, 0)
    target = deg_joints(0, 20, 0, 0, 0)

    duration = transport.early_lift_duration(start, target)

    assert duration > transport.LIFT_EARLY_MIN_DURATION_SEC
    assert peak_dps(start, target, duration) <= SERVO_PROFILE_VELOCITY_DPS
    peak_acceleration = (
        20.0 / duration**2 * transport.QUINTIC_PEAK_ACCELERATION_FACTOR
    )
    assert peak_acceleration <= SERVO_PROFILE_ACCEL_DPS2


def test_bin_rotation_is_independent_of_safe_approach_rotation(monkeypatch):
    monkeypatch.setattr(transport, "SAFE_APPROACH_PREALIGN_MIN_DURATION_SEC", 9.0)
    monkeypatch.setattr(
        transport.scan.multi, "movement_duration", lambda _delta: 99.0)
    stages = [deg_joints(0, 0, 0, 0, 0)] * 4
    arm = RecordingArm(stages[0])
    folded = deg_joints(10, 0, 0, 0, 0)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)

    transport.move_held_pumpkin_to_bin(arm, stages[0], stages)

    assert arm.moves[-1][1] == pytest.approx(1.5 / 1.3)


def test_deposit_with_taught_bin_poses(monkeypatch):
    monkeypatch.setattr(speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", False)
    monkeypatch.setattr(transport, "DROP_RAISE_M", 0.0)
    hover, drop, _drop_m = transport.load_adjusted_bin_poses()
    camera = transport.scan.base.load_calibrations()["camera_joints"]
    folded = np.asarray(camera, dtype=float).copy()
    folded[0] = hover[0]
    monkeypatch.setattr(transport, "_BIN_HOVER_JOINTS", hover)
    monkeypatch.setattr(transport, "_BIN_DROP_JOINTS", drop)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    sleeps = []
    arm = RecordingArm()
    monkeypatch.setattr(
        speed.time,
        "sleep",
        lambda seconds: (
            sleeps.append(seconds),
            arm.events.append(("sleep", seconds)),
        ),
    )

    default_gripper_value = 0.37
    speed.deposit_open_then_rise(
        arm, {"camera_joints": camera}, default_gripper_value, False)
    assert arm.grippers == [
        (default_gripper_value, speed.scan.grasp.GRIPPER_OPEN_DURATION_SEC),
        (default_gripper_value, 1.875),
    ]
    assert arm.gripper_calls[0] == (
        default_gripper_value,
        speed.scan.grasp.GRIPPER_OPEN_DURATION_SEC,
        {"stall_guard": True, "wait": True},
    )
    assert arm.gripper_calls[1][2] == {
        "stall_guard": False,
        "wait": True,
    }

    hover_s, descent_s, rise_s, fold_s = [d for _j, d in arm.moves]
    # ⑯c is already velocity-limited, so 1.3x is capped near 4.14 s.
    assert hover_s == pytest.approx(
        np.max(np.abs(np.degrees(hover - folded)))
        * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS)
    assert descent_s == pytest.approx(2.0)  # ⑰ j2 42.63 deg, floor
    assert rise_s == pytest.approx(1.95, abs=0.01)  # ⑲ j2 42.63 deg
    # Requested 3.0 s would exceed 41.2 deg/s; use the safe velocity floor.
    assert fold_s == pytest.approx(
        np.max(np.abs(np.degrees(folded - hover)))
        * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS)
    for start, (target, duration) in zip(
        (folded, hover, drop), arm.moves[:3]
    ):
        assert peak_dps(start, target, duration) <= (
            transport.SERVO_PROFILE_VELOCITY_DPS + 1e-9)
    # ⑯d, ⑰, ⑱, ⑲ settles stay 0.7 s; gripper stays open until after ⑲.
    assert sleeps == pytest.approx([0.7, 0.7, 0.7, 0.7])
    assert arm.events == [
        "move", ("sleep", 0.7),
        "move", ("sleep", 0.7),
        "release_gripper", ("sleep", 0.7),
        "move", ("sleep", 0.7),
        "restore_gripper", "move",
    ]


def test_direct_next_target_returns_at_bin_hover(monkeypatch):
    monkeypatch.setattr(speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", True)
    monkeypatch.setattr(transport, "DROP_RAISE_M", 0.0)
    hover, drop, _drop_m = transport.load_adjusted_bin_poses()
    camera = transport.scan.base.load_calibrations()["camera_joints"]
    folded = np.asarray(camera, dtype=float).copy()
    folded[0] = hover[0]
    monkeypatch.setattr(transport, "_BIN_HOVER_JOINTS", hover)
    monkeypatch.setattr(transport, "_BIN_DROP_JOINTS", drop)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    sleeps = []
    monkeypatch.setattr(speed.time, "sleep", sleeps.append)
    arm = RecordingArm(hover)

    speed.deposit_open_then_rise(
        arm, {"camera_joints": camera}, 0.37, False)

    assert len(arm.gripper_calls) == 1
    assert arm.gripper_calls[0][0] == pytest.approx(0.37)
    assert len(arm.moves) == 3
    np.testing.assert_array_equal(arm.moves[-1][0], hover)
    assert all(not np.array_equal(target, folded) for target, _d in arm.moves)
    assert sleeps == pytest.approx([0.7, 0.7, 0.7, 0.7])
    assert speed._direct_hover_pending


def test_direct_hover_cleanup_folds_from_actual_pose(monkeypatch):
    hover, folded, _camera = install_taught_bin(monkeypatch)
    arm = RecordingArm(hover)
    speed._direct_hover_pending = True

    recovered = speed.recover_direct_hover_for_cleanup(arm)

    assert recovered
    np.testing.assert_array_equal(arm.moves[-1][0], folded)
    assert not speed._direct_hover_pending


def test_cleanup_without_direct_hover_is_a_noop():
    arm = RecordingArm(deg_joints(0, 0, 0, 0, 0))

    recovered = speed.recover_direct_hover_for_cleanup(arm)

    assert not recovered
    assert arm.moves == []


def install_taught_bin(monkeypatch):
    monkeypatch.setattr(transport, "DROP_RAISE_M", 0.0)
    hover, drop, _drop_m = transport.load_adjusted_bin_poses()
    camera = np.asarray(
        transport.scan.base.load_calibrations()["camera_joints"], dtype=float)
    folded = camera.copy()
    folded[0] = hover[0]
    monkeypatch.setattr(transport, "_BIN_HOVER_JOINTS", hover)
    monkeypatch.setattr(transport, "_BIN_DROP_JOINTS", drop)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    monkeypatch.setattr(speed.time, "sleep", lambda _s: None)
    return hover, folded, camera


@pytest.mark.parametrize("direct_mode", [True, False])
def test_last_pumpkin_cleanup_uses_safe_dedicated_sequence(
    monkeypatch, direct_mode,
):
    monkeypatch.setattr(
        speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", direct_mode)
    hover, folded, camera = install_taught_bin(monkeypatch)
    monkeypatch.setattr(speed, "departure_signal_gate", lambda: None)
    sleeps = []
    monkeypatch.setattr(speed.time, "sleep", sleeps.append)
    arm = RecordingArm()

    default_gripper_value = 0.37
    speed.deposit_open_then_rise(
        arm, {"camera_joints": camera}, default_gripper_value, True)

    assert speed.LAST_PUMPKIN_GRIPPER_RESTORE_DURATION_SEC == pytest.approx(1.5)
    assert speed.LAST_PUMPKIN_FOLD_MIN_DURATION_SEC == pytest.approx(1.5)
    assert speed.LAST_PUMPKIN_CENTER_RETURN_DURATION_SEC == pytest.approx(1.7)
    assert speed.LAST_PUMPKIN_CENTER_SETTLE_SEC == pytest.approx(0.5)
    assert arm.grippers == [
        (default_gripper_value, speed.scan.grasp.GRIPPER_OPEN_DURATION_SEC),
        (default_gripper_value, 1.5),
    ]
    assert arm.gripper_calls[0][2] == {
        "stall_guard": True,
        "wait": True,
    }
    (fold_joints, fold_s), (center_joints, center_s) = arm.moves[-2:]
    np.testing.assert_array_equal(fold_joints, folded)
    np.testing.assert_array_equal(center_joints, camera)
    assert fold_s == pytest.approx(90.87890625 / SPEED)
    assert center_s == pytest.approx(1.7)
    assert sleeps[-1] == pytest.approx(0.5)
    assert sum((1.5, fold_s, center_s, sleeps[-1])) == pytest.approx(
        1.5 + 90.87890625 / SPEED + 1.7 + 0.5)
    assert peak_dps(hover, folded, 2.3) > SERVO_PROFILE_VELOCITY_DPS
    assert peak_dps(hover, folded, fold_s) <= SERVO_PROFILE_VELOCITY_DPS
    fold_delta = np.max(np.abs(np.degrees(folded - hover)))
    assert 5.7735 * fold_delta / fold_s**2 <= SERVO_PROFILE_ACCEL_DPS2


def test_park_keeps_omx_park_and_times_only_the_fold():
    camera = np.radians([-3.6, -51.94, 31.55, 70.22, -12.39])
    arm = RecordingArm(camera)

    speed.park_at_target_speed(arm)

    folded = speed.scan.omx_robot.FOLDED
    delta = np.max(np.abs(np.degrees(folded - camera)))  # j3 61.45 deg
    assert speed.PARK_MIN_DURATION_SEC == pytest.approx(1.5)
    assert arm.parks == [pytest.approx(delta / SPEED)]  # was 5.0 s
    assert arm.parks[0] == pytest.approx(2.806, abs=0.01)
    assert 5.7735 * delta / arm.parks[0] ** 2 <= SERVO_PROFILE_ACCEL_DPS2

    arm = RecordingArm(folded)
    speed.park_at_target_speed(arm)
    assert arm.parks == [pytest.approx(1.5)]
