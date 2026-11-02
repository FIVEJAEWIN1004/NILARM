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


class FeedbackArm(RecordingArm):
    def move_joints(self, joints, duration):
        super().move_joints(joints, duration)
        self.start = np.asarray(joints, dtype=float).copy()


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


def test_lift_and_bin_transport_keep_staged_waypoints_and_safe_2x(monkeypatch):
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

    transport.move_held_pumpkin_to_bin(arm, prealign, stages)

    assert len(arm.moves) == 5
    expected_targets = [plus10, plus30, plus80, prealign, folded]
    for (target, _duration), expected in zip(arm.moves, expected_targets):
        np.testing.assert_array_equal(target, expected)

    starts = [grasp, plus10, plus30, plus80, prealign]
    minimums = [0.5, 0.5, 0.8, 1.0, 1.0]
    for start, (target, duration), minimum in zip(
        starts, arm.moves, minimums
    ):
        assert duration >= minimum
        delta = np.max(np.abs(np.degrees(target - start)))
        assert delta / duration * 1.875 <= SERVO_PROFILE_VELOCITY_DPS
        assert (
            delta / duration**2 * transport.QUINTIC_PEAK_ACCELERATION_FACTOR
            <= SERVO_PROFILE_ACCEL_DPS2
        )

    # Short lift segments retain their established stability floor; larger
    # moves are limited by the servo-safe quintic time rather than forced 2x.
    assert [duration for _target, duration in arm.moves[:2]] == pytest.approx(
        [0.50, 0.50]
    )
    assert arm.moves[2][1] == pytest.approx(
        19.0 * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS
    )
    assert arm.moves[4][1] == pytest.approx(
        102.85 * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS
    )


def test_direct_lift_skips_intermediate_commands_and_stops_at_escape(
    monkeypatch,
):
    grasp = deg_joints(-126.4, 10, 20, 30, 0)
    plus10 = grasp + deg_joints(0, -3.4, -0.6, 4.0, 0)
    plus30 = plus10 + deg_joints(0, -5.8, -2.1, 7.9, 0)
    plus80 = plus30 + deg_joints(0, -8.5, -10.5, 19.0, 0)
    stages = [plus80, plus30, plus10, grasp]
    prealign = plus80 + deg_joints(0, -26.0, -4.4, -2.8, -14.4)
    folded = prealign.copy()
    folded[0] = np.radians(-23.55)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    monkeypatch.setattr(
        transport, "direct_lift_to_escape_enabled", lambda: True
    )
    arm = RecordingArm(grasp)

    expected_plan = transport.plan_direct_lift_to_escape(
        arm, grasp, stages, prealign
    )
    transport.move_held_pumpkin_to_bin(arm, prealign, stages)

    assert len(arm.moves) == 1
    np.testing.assert_array_equal(arm.moves[0][0], folded)
    assert arm.streamed
    np.testing.assert_allclose(arm.streamed[-1], prealign)
    via40 = expected_plan["segments"][0][0]
    expected_via40 = plus30 + 0.2 * (plus80 - plus30)
    np.testing.assert_allclose(via40, expected_via40)
    assert not any(np.array_equal(point, plus80) for point in arm.streamed)


def test_direct_lift_plan_failure_restores_all_staged_waypoints(monkeypatch):
    grasp = deg_joints(-126.4, 10, 20, 30, 0)
    plus10 = grasp + deg_joints(0, -3.4, -0.6, 4.0, 0)
    plus30 = plus10 + deg_joints(0, -5.8, -2.1, 7.9, 0)
    plus80 = plus30 + deg_joints(0, -8.5, -10.5, 19.0, 0)
    stages = [plus80, plus30, plus10, grasp]
    prealign = plus80.copy()
    folded = prealign.copy()
    folded[0] = np.radians(-23.55)
    monkeypatch.setattr(transport, "_BIN_FOLDED_JOINTS", folded)
    monkeypatch.setattr(
        transport, "direct_lift_to_escape_enabled", lambda: True
    )
    monkeypatch.setattr(
        transport,
        "plan_direct_lift_to_escape",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("직접 리프트 검증 실패")
        ),
    )
    arm = RecordingArm(grasp)

    transport.move_held_pumpkin_to_bin(arm, prealign, stages)

    for (target, _duration), expected in zip(
        arm.moves[:3], (plus10, plus30, plus80)
    ):
        np.testing.assert_array_equal(target, expected)


def test_held_floors():
    assert transport.HELD_MOVE_SPEEDUP == pytest.approx(2.0)
    assert transport.LIFT_STEP_MIN_DURATION_SEC == pytest.approx(0.8)
    assert transport.LIFT_EARLY_SPEEDUP == pytest.approx(1.7)
    assert transport.LIFT_EARLY_MIN_DURATION_SEC == pytest.approx(0.5)
    assert transport.HELD_BIN_MOVE_SPEEDUP == pytest.approx(2.0)
    assert transport.HELD_FOLD_MIN_DURATION_SEC == pytest.approx(1.0)
    assert transport.HELD_BIN_ROTATION_MIN_DURATION_SEC == pytest.approx(1.0)
    assert speed.BIN_HOVER_MIN_DURATION_SEC == pytest.approx(1.0)
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

    assert arm.moves[-1][1] == pytest.approx(1.0)


def test_deposit_with_taught_bin_poses(monkeypatch):
    assert speed.BIN_RELEASE_GRIPPER_SPEEDUP == pytest.approx(3.0)
    assert speed.BIN_RELEASE_GRIPPER_DURATION_SEC == pytest.approx(1.0)
    assert speed.BIN_GRIPPER_RESTORE_EXTRA_SPEEDUP == pytest.approx(2.0)
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
        (default_gripper_value, speed.BIN_RELEASE_GRIPPER_DURATION_SEC),
        (default_gripper_value, 0.9375),
    ]
    assert arm.gripper_calls[0] == (
        default_gripper_value,
        speed.BIN_RELEASE_GRIPPER_DURATION_SEC,
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
    # Motion waypoints pause for 0.3 s; fruit release keeps its 0.7 s wait.
    assert sleeps == pytest.approx([0.3, 0.3, 0.7, 0.3])
    assert arm.events == [
        "move", ("sleep", 0.3),
        "move", ("sleep", 0.3),
        "release_gripper", ("sleep", 0.7),
        "move", ("sleep", 0.3),
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
    assert sleeps == pytest.approx([0.3, 0.3, 0.7, 0.3])
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
    monkeypatch.setattr(speed, "DIRECT_LAST_HOVER_TO_PARK", False)
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
    assert speed.LAST_PUMPKIN_CLEANUP_SPEEDUP == pytest.approx(3.0)
    assert arm.grippers == [
        (default_gripper_value, speed.BIN_RELEASE_GRIPPER_DURATION_SEC),
        (default_gripper_value, 0.25),
    ]
    assert arm.gripper_calls[0][2] == {
        "stall_guard": True,
        "wait": True,
    }
    (fold_joints, fold_s), (center_joints, center_s) = arm.moves[-2:]
    np.testing.assert_array_equal(fold_joints, folded)
    np.testing.assert_array_equal(center_joints, camera)
    fold_delta = np.max(np.abs(np.degrees(folded - hover)))
    center_delta = np.max(np.abs(np.degrees(camera - folded)))
    assert fold_s == pytest.approx(
        fold_delta * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS
    )
    assert center_s == pytest.approx(
        center_delta * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS
    )
    assert sleeps[-1] == pytest.approx(0.5)
    assert arm.events.index("restore_gripper") < len(arm.events) - 2
    assert peak_dps(hover, folded, 2.3) > SERVO_PROFILE_VELOCITY_DPS
    assert peak_dps(hover, folded, fold_s) <= SERVO_PROFILE_VELOCITY_DPS
    assert 5.7735 * fold_delta / fold_s**2 <= SERVO_PROFILE_ACCEL_DPS2
    assert peak_dps(folded, camera, center_s) <= SERVO_PROFILE_VELOCITY_DPS
    assert 5.7735 * center_delta / center_s**2 <= SERVO_PROFILE_ACCEL_DPS2


def test_park_keeps_omx_park_and_times_only_the_fold():
    camera = np.radians([-3.6, -51.94, 31.55, 70.22, -12.39])
    arm = RecordingArm(camera)
    speed._last_pumpkin_cleanup_completed = True

    speed.park_at_target_speed(arm)

    folded = speed.scan.omx_robot.FOLDED
    delta = np.max(np.abs(np.degrees(folded - camera)))  # j3 61.45 deg
    assert speed.PARK_MIN_DURATION_SEC == pytest.approx(1.5)
    assert arm.parks == [pytest.approx(
        delta * 1.875 / transport.SERVO_PROFILE_VELOCITY_DPS
    )]
    assert arm.parks[0] == pytest.approx(2.797, abs=0.01)
    assert 5.7735 * delta / arm.parks[0] ** 2 <= SERVO_PROFILE_ACCEL_DPS2

    arm = RecordingArm(folded)
    speed._last_pumpkin_cleanup_completed = True
    speed.park_at_target_speed(arm)
    assert arm.parks == [pytest.approx(1.5)]


def test_direct_last_fold_to_park_uses_actual_fold_feedback(monkeypatch):
    hover, folded, camera = install_taught_bin(monkeypatch)
    monkeypatch.setattr(speed, "DIRECT_LAST_HOVER_TO_PARK", False)
    monkeypatch.setattr(speed, "DIRECT_LAST_FOLD_TO_PARK", True)
    monkeypatch.setattr(speed, "departure_signal_gate", lambda: None)
    arm = FeedbackArm(hover)

    speed.deposit_open_then_rise(
        arm, {"camera_joints": camera}, 0.37, True
    )

    np.testing.assert_array_equal(arm.moves[-1][0], folded)
    assert all(not np.array_equal(target, camera) for target, _ in arm.moves)
    assert speed._direct_last_park_pending
    expected = speed.last_cleanup_duration_3x(
        folded,
        speed.scan.omx_robot.FOLDED,
        current_duration=transport.duration_for_target_joint_speed(
            folded,
            speed.scan.omx_robot.FOLDED,
            min_duration=speed.PARK_MIN_DURATION_SEC,
        ),
        minimum_duration=speed.PARK_MIN_DURATION_SEC,
    )
    assert speed._direct_last_park_duration == pytest.approx(expected)

    speed.park_at_target_speed(arm)

    assert arm.parks == [pytest.approx(expected)]
    assert not speed._direct_last_park_pending


@pytest.mark.parametrize("direct_enabled", [False, True])
def test_direct_last_park_disabled_or_invalid_uses_center_fallback(
    monkeypatch, direct_enabled,
):
    hover, folded, camera = install_taught_bin(monkeypatch)
    monkeypatch.setattr(speed, "DIRECT_LAST_HOVER_TO_PARK", False)
    monkeypatch.setattr(speed, "DIRECT_LAST_FOLD_TO_PARK", direct_enabled)
    monkeypatch.setattr(speed, "departure_signal_gate", lambda: None)
    if direct_enabled:
        monkeypatch.setattr(
            speed,
            "plan_direct_last_fold_to_park",
            lambda _arm: (_ for _ in ()).throw(
                ValueError("직접 PARK 검증 실패")
            ),
        )
    arm = FeedbackArm(hover)

    speed.deposit_open_then_rise(
        arm, {"camera_joints": camera}, 0.37, True
    )

    np.testing.assert_array_equal(arm.moves[-2][0], folded)
    np.testing.assert_array_equal(arm.moves[-1][0], camera)
    assert not speed._direct_last_park_pending


def test_non_last_or_error_park_keeps_existing_duration():
    camera = np.radians([-3.6, -51.94, 31.55, 70.22, -12.39])
    arm = RecordingArm(camera)
    speed._last_pumpkin_cleanup_completed = False

    speed.park_at_target_speed(arm)

    assert arm.parks == [pytest.approx(
        transport.duration_for_target_joint_speed(
            camera,
            speed.scan.omx_robot.FOLDED,
            min_duration=speed.PARK_MIN_DURATION_SEC,
        )
    )]
