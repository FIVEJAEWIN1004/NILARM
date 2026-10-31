"""Hardware-free tests for optional harvest timing and planning optimizations."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_auto_scan_count_orange_harvest as scan,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as harvest,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += float(seconds)


class FeedbackArm:
    def __init__(self, samples):
        self.samples = iter(samples)
        self.last = np.asarray(samples[-1], dtype=float)

    def joints(self):
        try:
            self.last = np.asarray(next(self.samples), dtype=float)
        except StopIteration:
            pass
        return self.last


def install_clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(harvest.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(harvest.time, "sleep", clock.sleep)
    return clock


def test_adaptive_settle_exits_early_when_feedback_is_stable(monkeypatch):
    clock = install_clock(monkeypatch)
    target = np.zeros(5)
    arm = FeedbackArm([target] * 8)

    settled = harvest.wait_until_arm_settled(
        arm,
        target,
        min_settle_sec=0.10,
        max_settle_sec=0.70,
        stable_window_sec=0.15,
    )

    assert settled
    assert 0.25 <= clock.now < 0.70


def test_adaptive_settle_keeps_original_timeout_when_unstable(monkeypatch):
    clock = install_clock(monkeypatch)
    target = np.zeros(5)
    moving = [np.radians([0, value, 0, 0, 0]) for value in range(20)]

    settled = harvest.wait_until_arm_settled(
        FeedbackArm(moving),
        target,
        min_settle_sec=0.10,
        max_settle_sec=0.70,
    )

    assert not settled
    assert clock.now == pytest.approx(0.70)


def test_adaptive_settle_invalid_feedback_falls_back_to_timeout(monkeypatch):
    clock = install_clock(monkeypatch)
    invalid = np.asarray([0, np.nan, 0, 0, 0])

    settled = harvest.wait_until_arm_settled(
        FeedbackArm([invalid]),
        np.zeros(5),
        min_settle_sec=0.10,
        max_settle_sec=0.70,
    )

    assert not settled
    assert clock.now == pytest.approx(0.70)


def test_adaptive_settle_honours_cancel(monkeypatch):
    install_clock(monkeypatch)

    with pytest.raises(scan.ScanCancelled):
        harvest.wait_until_arm_settled(
            FeedbackArm([np.zeros(5)]),
            np.zeros(5),
            min_settle_sec=0.10,
            max_settle_sec=0.70,
            cancel_callback=lambda: True,
        )


def detection(x, y, angle):
    return scan.Detection(
        target={"world_target_xy": [x, y], "planned_grasp_z": 0.02},
        label="ORANGE",
        orange_ratio=0.9,
        green_ratio=0.0,
        confidence=0.9,
        image_margin_px=40.0,
        commanded_offset_deg=float(angle),
        measured_offset_deg=float(angle),
    )


def cluster(x, y, *angles):
    return scan.PumpkinCluster(
        x=x,
        y=y,
        observations=[detection(x, y, angle) for angle in angles],
    )


def fake_solve(cost_by_x, rejected_x=()):
    def solve(_arm, _calibration, item, _current, **_kwargs):
        if item.x in rejected_x:
            raise ValueError("joint3 절대 한계 초과")
        target = {"world_target_xy": [item.x, item.y], "xyz_stages": []}
        joints = np.zeros(5)
        cost = float(cost_by_x[item.x])
        return (
            item.best_orange(), target, -50, joints, 0.0,
            [joints] * 4, [], cost / 2.0, cost / 2.0,
        )

    return solve


def test_preplanning_rejects_invalid_targets_before_motion(monkeypatch):
    items = [cluster(0.1, 0.0, -50), cluster(0.2, 0.0, -50)]
    monkeypatch.setattr(
        harvest,
        "solve_harvest_approach",
        fake_solve({0.1: 3.0, 0.2: 4.0}, rejected_x={0.2}),
    )
    arm = FeedbackArm([np.zeros(5)])

    plans = harvest.precompute_harvest_plans(
        arm, {}, items, bypass_high_delta_guard=True
    )

    assert [plan.valid for plan in plans] == [True, False]
    assert "joint3" in plans[1].rejection_reason
    assert harvest.order_precomputed_harvest_plans(
        plans, optimize_joint_cost=True
    )[0].cluster is items[0]


def test_joint_cost_order_and_distance_fallback_are_deterministic(monkeypatch):
    near = cluster(0.1, 0.0, -50)
    far_fast = cluster(0.3, 0.0, -50)
    monkeypatch.setattr(
        harvest,
        "solve_harvest_approach",
        fake_solve({0.1: 5.0, 0.3: 2.0}),
    )
    plans = harvest.precompute_harvest_plans(
        FeedbackArm([np.zeros(5)]),
        {},
        [near, far_fast],
        bypass_high_delta_guard=True,
    )

    assert [plan.cluster for plan in harvest.order_precomputed_harvest_plans(
        plans, optimize_joint_cost=True
    )] == [far_fast, near]
    assert [plan.cluster for plan in harvest.order_precomputed_harvest_plans(
        plans, optimize_joint_cost=False
    )] == [near, far_fast]


def test_scan_early_exit_is_disabled_for_harvest_all(monkeypatch):
    confirmed = cluster(0.1, 0.0, -50, -80)
    monkeypatch.setattr(speed, "ENABLE_ADAPTIVE_SCAN_EARLY_EXIT", True)

    assert not speed.should_end_scan_early([confirmed], None)
    assert speed.should_end_scan_early([confirmed], 1)
    monkeypatch.setattr(speed, "ENABLE_ADAPTIVE_SCAN_EARLY_EXIT", False)
    assert not speed.should_end_scan_early([confirmed], 1)


def test_release_wait_stays_fixed_when_adaptive_arm_settle_enabled(monkeypatch):
    monkeypatch.setattr(speed, "ENABLE_ADAPTIVE_ARM_SETTLE", True)
    hover = np.zeros(5)
    drop = np.radians([0, 10, 0, 0, 0])
    folded = np.radians([20, 0, 0, 0, 0])
    monkeypatch.setattr(harvest, "_BIN_HOVER_JOINTS", hover)
    monkeypatch.setattr(harvest, "_BIN_DROP_JOINTS", drop)
    monkeypatch.setattr(harvest, "_BIN_FOLDED_JOINTS", folded)
    monkeypatch.setattr(speed, "DIRECT_NEXT_TARGET_FROM_BIN_HOVER", True)
    settled_targets = []
    monkeypatch.setattr(
        harvest,
        "wait_until_arm_settled",
        lambda _arm, target, **_kwargs: settled_targets.append(target) or True,
    )
    fixed_sleeps = []
    monkeypatch.setattr(speed.time, "sleep", fixed_sleeps.append)

    class Arm:
        kin = None

        def move_joints(self, *_args, **_kwargs):
            pass

        def gripper(self, *_args, **_kwargs):
            pass

    speed.deposit_open_then_rise(Arm(), {"camera_joints": hover}, 0.37, False)

    assert len(settled_targets) == 3
    assert fixed_sleeps == [speed.BIN_SETTLE_SEC]


def test_optimization_defaults_keep_hardware_dependent_features_off():
    assert speed.ENABLE_PRECOMPUTED_HARVEST_PLANS
    assert speed.ENABLE_JOINT_COST_TARGET_ORDER
    assert not speed.ENABLE_ADAPTIVE_ARM_SETTLE
    assert not speed.ENABLE_ADAPTIVE_SCAN_SETTLE
    assert not speed.ENABLE_ADAPTIVE_SCAN_EARLY_EXIT
    assert not speed.ENABLE_CONTINUOUS_SAFE_APPROACH
