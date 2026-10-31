"""First scan entry and pumpkin preposition speed tests."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as harvest,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


def test_first_minus_140_scan_entry_is_twice_current_scan_speed():
    current = speed.scan_step_rotation_duration(-140.0)
    accelerated = speed.scan_target_rotation_duration(-140.0, -140.0)

    assert accelerated == pytest.approx(current / 2.0)


def test_other_scan_targets_keep_current_scan_speed():
    assert speed.scan_target_rotation_duration(-110.0, 30.0) == pytest.approx(
        speed.scan_step_rotation_duration(30.0)
    )
    assert speed.scan_target_rotation_duration(130.0, 30.0) == pytest.approx(
        speed.scan_step_rotation_duration(30.0)
    )


def deg_joints(*values):
    return np.radians(np.asarray(values, dtype=float))


class ApproachArm:
    def __init__(self, start):
        self.start = start
        self.moves = []
        self.close_calls = []

    def joints(self):
        return self.start

    def move_joints(self, joints, duration):
        self.moves.append((np.asarray(joints, dtype=float), float(duration)))

    def close_gripper(self, **_kwargs):
        self.close_calls.append(_kwargs)


def run_safe_approach(monkeypatch, start, prealign, high):
    detection = harvest.scan.Detection(
        target={"world_target_xy": [0.17, 0.0], "planned_grasp_z": 0.02},
        label="ORANGE",
        orange_ratio=0.9,
        green_ratio=0.0,
        confidence=0.9,
        image_margin_px=50.0,
        commanded_offset_deg=-50.0,
        measured_offset_deg=-50.0,
    )
    cluster = harvest.scan.PumpkinCluster(
        x=0.17, y=0.0, observations=[detection])
    stages = [high] + [high + deg_joints(0, i, 0, 0, 0) for i in (1, 2, 3)]
    monkeypatch.setattr(
        harvest.scan.multi,
        "plan_fixed_pose_stages_from_folded_pose",
        lambda *_args, **_kwargs: (prealign, 0.0, stages, None),
    )
    monkeypatch.setattr(harvest, "move_held_pumpkin_to_bin", lambda *_a: None)
    monkeypatch.setattr(harvest, "deposit_and_prepare_next", lambda *_a, **_k: None)
    arm = ApproachArm(start)
    assert harvest.harvest_one_direct(
        arm, {"pitch_rad": 0.0, "roll_rad": 0.0}, cluster, 0.3, 1, 1)
    return arm


def test_safe_approach_target_speed_and_floors():
    assert harvest.TARGET_AVERAGE_JOINT_SPEED_DPS == pytest.approx(21.9)
    assert harvest.TARGET_AVERAGE_JOINT_SPEED_DPS * 1.875 <= 41.2
    assert harvest.SAFE_APPROACH_PREALIGN_MIN_DURATION_SEC == pytest.approx(1.2)
    assert harvest.SAFE_APPROACH_HIGH_MIN_DURATION_SEC == pytest.approx(1.4)
    assert harvest.SAFE_APPROACH_SPEEDUP == pytest.approx(1.3)


@pytest.mark.parametrize(
    ("start_j1", "target_j1", "expected"),
    [
        (-3.6, -126.4, 122.8 * 1.875 / 41.2),
        (-23.55, -126.4, 102.85 * 1.875 / 41.2),
        (
            -23.55,
            0.55,
            24.1 * harvest.QUINTIC_PEAK_VELOCITY_FACTOR
            / harvest.SERVO_PROFILE_VELOCITY_DPS,
        ),
    ],
)
def test_prealign_uses_joint1_change_from_actual_start(
    monkeypatch, start_j1, target_j1, expected
):
    folded = deg_joints(start_j1, -51.94, 31.55, 70.22, -12.39)
    prealign = folded.copy()
    prealign[0] = np.radians(target_j1)
    high = prealign + deg_joints(0, 34.7, 4.2, 2.6, 14.4)

    arm = run_safe_approach(monkeypatch, folded, prealign, high)
    moves = arm.moves

    assert moves[0][1] == pytest.approx(expected)
    # ⑫b reaches the servo-safe quintic velocity floor.
    assert moves[1][1] == pytest.approx(34.7 * 1.875 / 41.2)
    # ⑬ keeps three stop-to-stop waypoints with independent durations.
    assert [d for _j, d in moves[2:]] == pytest.approx((2.5, 2.0, 2.0))
    assert sum(d for _j, d in moves[2:]) == pytest.approx(6.5)
    assert 16.6 - sum(d for _j, d in moves[2:]) == pytest.approx(10.1)
    assert 21.6 - sum(d for _j, d in moves[2:]) == pytest.approx(15.1)
    expected_stages = [
        high + deg_joints(0, index, 0, 0, 0) for index in (1, 2, 3)
    ]
    for (target, _duration), expected in zip(moves[2:], expected_stages):
        np.testing.assert_array_equal(target, expected)
    assert arm.close_calls == [{
        "duration": harvest.scan.grasp.GRIPPER_CLOSE_DURATION_SEC,
        "stall_guard": True,
        "wait": True,
    }]
    assert harvest.scan.grasp.GRIPPER_CLOSE_DURATION_SEC == pytest.approx(4.0)


def test_short_high_approach_keeps_floor(monkeypatch):
    folded = deg_joints(0, -51.94, 31.55, 70.22, -12.39)
    high = folded + deg_joints(0, 10, 0, 0, 0)

    moves = run_safe_approach(monkeypatch, folded, folded, high).moves

    assert moves[1][1] == pytest.approx(1.4 / 1.3)


def test_continuous_safe_approach_keeps_both_waypoints(monkeypatch):
    folded = deg_joints(0, -51.94, 31.55, 70.22, -12.39)
    prealign = folded.copy()
    prealign[0] = np.radians(-80.0)
    high = prealign + deg_joints(0, 20, 4, 6, 2)
    captured = []
    monkeypatch.setattr(
        harvest, "continuous_safe_approach_enabled", lambda: True
    )
    monkeypatch.setattr(
        harvest.joint_trajectory,
        "move_joints_continuous",
        lambda _arm, segments, via_speed_caps_dps: (
            captured.extend(segments),
            captured.append(tuple(via_speed_caps_dps)),
            0,
        )[-1],
    )

    arm = run_safe_approach(monkeypatch, folded, prealign, high)

    np.testing.assert_array_equal(captured[0][0], prealign)
    np.testing.assert_array_equal(captured[1][0], high)
    assert captured[2] == (0.0,)
    # Only the three ⑬ stop-to-stop descents remain as move_joints calls.
    assert len(arm.moves) == 3


def test_continuous_safe_approach_validation_failure_uses_old_path(
    monkeypatch,
):
    folded = deg_joints(0, -51.94, 31.55, 70.22, -12.39)
    prealign = folded.copy()
    prealign[0] = np.radians(-80.0)
    high = prealign + deg_joints(0, 20, 4, 6, 2)
    monkeypatch.setattr(
        harvest, "continuous_safe_approach_enabled", lambda: True
    )
    monkeypatch.setattr(
        harvest.joint_trajectory,
        "move_joints_continuous",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("연속 궤적 검증 실패")
        ),
    )

    moves = run_safe_approach(
        monkeypatch, folded, prealign, high
    ).moves

    np.testing.assert_array_equal(moves[0][0], prealign)
    np.testing.assert_array_equal(moves[1][0], high)
    assert len(moves) == 5


def test_continuous_safe_approach_100hz_path_stays_within_limits():
    start = deg_joints(-23.55, -15.38, -21.53, 98.44, 78.49)
    prealign = start.copy()
    prealign[0] = np.radians(-126.4)
    high = prealign + deg_joints(0, 34.7, 4.2, 2.6, 14.4)
    durations = [
        harvest.duration_with_safe_speedup(
            start,
            prealign,
            min_duration=harvest.SAFE_APPROACH_PREALIGN_MIN_DURATION_SEC,
            speedup=harvest.SAFE_APPROACH_SPEEDUP,
        ),
        harvest.duration_with_safe_speedup(
            prealign,
            high,
            min_duration=harvest.SAFE_APPROACH_HIGH_MIN_DURATION_SEC,
            speedup=harvest.SAFE_APPROACH_SPEEDUP,
        ),
    ]
    rounded, _via, coefficients = harvest.joint_trajectory.plan(
        start,
        [prealign, high],
        durations,
        [0.0],
        100.0,
    )
    points = list(harvest.joint_trajectory.sample_path(
        [prealign, high], rounded, coefficients, 100.0
    ))
    first_knot = round(rounded[0] * 100.0) - 1
    np.testing.assert_array_equal(points[first_knot], prealign)
    np.testing.assert_array_equal(points[-1], high)

    path_deg = np.degrees(np.asarray([start] + points))
    velocity = np.diff(path_deg, axis=0) * 100.0
    acceleration = np.diff(velocity, axis=0) * 100.0
    assert np.max(np.abs(velocity)) <= harvest.SERVO_PROFILE_VELOCITY_DPS
    assert np.max(np.abs(acceleration)) <= (
        harvest.SERVO_PROFILE_ACCELERATION_DPS2
    )


def test_final_approach_representative_ik_stays_within_servo_limits():
    grasp = deg_joints(-126.4, 10, 20, 30, 0)
    plus10 = grasp + deg_joints(0, -3.4, -0.6, 4.0, 0)
    plus30 = plus10 + deg_joints(0, -5.8, -2.1, 7.9, 0)
    plus80 = plus30 + deg_joints(0, -8.5, -10.5, 19.0, 0)
    stages = (plus80, plus30, plus10, grasp)

    assert harvest.FINAL_APPROACH_DURATIONS_SEC == (2.5, 2.0, 2.0)
    for start, target, duration in zip(
        stages,
        stages[1:],
        harvest.FINAL_APPROACH_DURATIONS_SEC,
    ):
        max_delta_deg = np.max(np.abs(np.degrees(target - start)))
        peak_velocity = (
            max_delta_deg / duration
            * harvest.QUINTIC_PEAK_VELOCITY_FACTOR
        )
        peak_acceleration = (
            max_delta_deg / duration**2
            * harvest.QUINTIC_PEAK_ACCELERATION_FACTOR
        )
        assert peak_velocity <= harvest.SERVO_PROFILE_VELOCITY_DPS
        assert peak_acceleration <= harvest.SERVO_PROFILE_ACCELERATION_DPS2


def test_prealign_uses_actual_bin_hover_joints_and_changes_only_joint1(
    monkeypatch,
):
    hover = deg_joints(-23.55, -15.38, -21.53, 98.44, 78.49)
    first_ik = hover.copy()
    first_ik[0] = np.radians(-126.4)
    later_ik = iter([
        first_ik + deg_joints(0, 3.0, 2.0, -4.0, 0),
        first_ik + deg_joints(0, 5.0, 3.0, -6.0, 0),
        first_ik + deg_joints(0, 7.0, 4.0, -8.0, 0),
    ])
    monkeypatch.setattr(
        harvest.scan.multi,
        "inverse_with_wrapped_joint1",
        lambda _arm, _xyz, seed, _pitch, _roll: (
            first_ik if np.array_equal(seed, hover) else next(later_ik)
        ),
    )

    prealign, _delta, stages, _deltas = (
        harvest.scan.multi.plan_fixed_pose_stages_from_folded_pose(
            object(),
            [np.zeros(3) for _ in range(4)],
            hover,
            0.0,
            0.0,
        )
    )

    assert prealign[0] == pytest.approx(first_ik[0])
    np.testing.assert_array_equal(prealign[1:], hover[1:])
    np.testing.assert_array_equal(stages[0], first_ik)


def plan_with_joint_targets(monkeypatch, targets, *, bypass=False):
    target_iter = iter(np.radians(np.asarray(targets, dtype=float)))
    monkeypatch.setattr(
        harvest.scan.multi,
        "inverse_with_wrapped_joint1",
        lambda *_args: next(target_iter),
    )
    return harvest.scan.multi.plan_fixed_pose_stages_from_folded_pose(
        object(),
        [np.zeros(3) for _ in targets],
        np.zeros(5),
        0.0,
        0.0,
        bypass_high_delta_guard=bypass,
    )


def test_folded_path_keeps_high_single_joint_delta_guard(monkeypatch):
    targets = [[0, 66, 0, 0, 0]] * 4

    with pytest.raises(ValueError, match="80mm 접근 단일 관절 변화 66.0도"):
        plan_with_joint_targets(monkeypatch, targets)


def test_folded_path_keeps_high_total_joint_delta_guard(monkeypatch):
    targets = [[0, 45, 45, 45, 45]] * 4

    with pytest.raises(ValueError, match="80mm 접근 전체 관절 변화 180.0도"):
        plan_with_joint_targets(monkeypatch, targets)


@pytest.mark.parametrize(
    "first_target",
    (
        [0, 76.1, 0, 0, 0],
        [0, 45, 45, 45, 45],
    ),
)
def test_direct_hover_bypasses_only_high_delta_guards(
    monkeypatch, first_target
):
    _prealign, _delta, stages, _deltas = plan_with_joint_targets(
        monkeypatch,
        [first_target] * 4,
        bypass=True,
    )

    np.testing.assert_allclose(
        np.degrees(stages[0]), first_target, atol=1e-12
    )


def test_direct_hover_keeps_lower_stage_delta_guard(monkeypatch):
    targets = [
        [0, 0, 0, 0, 0],
        [0, 26, 0, 0, 0],
        [0, 26, 0, 0, 0],
        [0, 26, 0, 0, 0],
    ]

    with pytest.raises(ValueError, match="하강 단일 관절 변화 26.0도"):
        plan_with_joint_targets(monkeypatch, targets, bypass=True)


def test_direct_hover_keeps_nonfinite_ik_rejection(monkeypatch):
    targets = [[0, np.nan, 0, 0, 0]] * 4

    with pytest.raises(ValueError, match="IK 결과가 올바르지 않습니다"):
        plan_with_joint_targets(monkeypatch, targets, bypass=True)


def test_direct_hover_keeps_absolute_joint1_limit():
    class OutOfLimitKinematics:
        def inverse(self, *_args, **_kwargs):
            return deg_joints(151, 0, 0, 0, 0)

        def analytic(self, *_args, **_kwargs):
            raise ValueError("no valid analytic solution")

    arm = type("Arm", (), {"kin": OutOfLimitKinematics()})()

    with pytest.raises(ValueError, match="joint1 안전 한계"):
        harvest.scan.multi.inverse_with_wrapped_joint1(
            arm, np.zeros(3), np.zeros(5), 0.0, 0.0
        )


def test_76_degree_direct_approach_uses_servo_safe_duration():
    start = np.zeros(5)
    target = deg_joints(0, 76.1, 0, 0, 0)
    calculated_duration = harvest.duration_with_safe_speedup(
        start,
        target,
        min_duration=harvest.SAFE_APPROACH_HIGH_MIN_DURATION_SEC,
        speedup=harvest.SAFE_APPROACH_SPEEDUP,
    )
    duration = np.ceil(calculated_duration * 100.0) / 100.0
    average_speed = 76.1 / duration
    peak_speed = average_speed * harvest.QUINTIC_PEAK_VELOCITY_FACTOR
    peak_acceleration = (
        76.1 / duration**2 * harvest.QUINTIC_PEAK_ACCELERATION_FACTOR
    )

    assert duration >= 76.1 * 1.875 / 41.2
    assert calculated_duration == pytest.approx(3.4632888350)
    assert duration == pytest.approx(3.47)
    assert peak_speed <= harvest.SERVO_PROFILE_VELOCITY_DPS
    assert peak_acceleration <= harvest.SERVO_PROFILE_ACCELERATION_DPS2


def test_direct_guard_bypass_requires_all_three_conditions(monkeypatch):
    monkeypatch.setattr(speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", True)
    monkeypatch.setattr(
        speed, "DIRECT_HOVER_BYPASS_APPROACH_DELTA_GUARD", True
    )
    monkeypatch.setattr(speed, "_direct_hover_pending", True)
    assert speed.should_bypass_direct_hover_approach_delta_guard()

    monkeypatch.setattr(speed, "_direct_hover_pending", False)
    assert not speed.should_bypass_direct_hover_approach_delta_guard()
    monkeypatch.setattr(speed, "_direct_hover_pending", True)
    monkeypatch.setattr(speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", False)
    assert not speed.should_bypass_direct_hover_approach_delta_guard()
    monkeypatch.setattr(speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", True)
    monkeypatch.setattr(
        speed, "DIRECT_HOVER_BYPASS_APPROACH_DELTA_GUARD", False
    )
    assert not speed.should_bypass_direct_hover_approach_delta_guard()
