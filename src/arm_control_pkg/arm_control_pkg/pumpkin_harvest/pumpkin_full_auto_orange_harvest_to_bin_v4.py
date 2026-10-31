#!/usr/bin/env python3
"""Full-auto orange harvest v4 with selective arm speeds.

The newly re-taught bin poses are used exactly as saved.  Preparation and
normal arm transit run 1.5x faster than the v3 speed.  Moves into scan views
run another 2.704x faster and the post-scan return another 2.08x.  Bin hover,
bin descent and the open-gripper rise are timed from their joint change at
v2.TARGET_AVERAGE_JOINT_SPEED_DPS.  Pumpkin descent retains the v3
speed.  Gripper timing is unchanged.  After release, the gripper rises to bin
hover; the experimental non-last path can continue directly from there.
"""

from __future__ import annotations

import time

import numpy as np

from . import pumpkin_auto_scan_count_orange_harvest as scan
from . import pumpkin_full_auto_orange_harvest_to_bin_v2 as v2


# v3 used 0.90 of the original duration.  Dividing that duration by 1.5 gives
# 0.60 of the original duration for all non-descent arm motions.
TRANSIT_DURATION_FACTOR = 0.60
# Post-scan return to centre (and cancel return) keep the 2.08x speed.
SCAN_EXTRA_SPEED_MULTIPLIER = 2.08
POST_SCAN_RETURN_SPEEDUP = 2.0
# Moves between scan views run another 1.3x faster than the return.
SCAN_STEP_SPEED_MULTIPLIER = SCAN_EXTRA_SPEED_MULTIPLIER * 1.3
FIRST_SCAN_ENTRY_SPEED_MULTIPLIER = 2.0
SCAN_ROTATION_DURATION_FACTOR = (
    TRANSIT_DURATION_FACTOR / SCAN_EXTRA_SPEED_MULTIPLIER
)
SCAN_STEP_DURATION_FACTOR = (
    TRANSIT_DURATION_FACTOR / SCAN_STEP_SPEED_MULTIPLIER
)
DESCENT_DURATION_FACTOR = 0.90
MIN_ROTATION_DURATION_SEC = 2.0

BIN_HOVER_MIN_DURATION_SEC = 1.5
BIN_DESCENT_MIN_DURATION_SEC = 2.0
OPEN_GRIPPER_RISE_MIN_DURATION_SEC = 1.9
# ㉑ cleanup keeps the fold on the shared 21.9 deg/s safety limit.
LAST_PUMPKIN_GRIPPER_RESTORE_DURATION_SEC = 1.5
LAST_PUMPKIN_FOLD_MIN_DURATION_SEC = 1.5
LAST_PUMPKIN_CENTER_RETURN_DURATION_SEC = 1.7
LAST_PUMPKIN_CENTER_SETTLE_SEC = 0.5
PARK_MIN_DURATION_SEC = 1.5
BIN_FOLD_DURATION_SEC = 8.0 * TRANSIT_DURATION_FACTOR
NEXT_TARGET_GRIPPER_RESTORE_DURATION_SEC = 3.0 / 1.6
NEXT_TARGET_FOLD_SPEEDUP = 1.6
BIN_SETTLE_SEC = 0.7
DIRECT_NEXT_TARGET_FROM_BIN_HOVER = True
# ㉔ Pinky departs as soon as the LAST pumpkin's open gripper has risen to the
# bin hover pose and settled (⑲ + BIN_SETTLE_SEC): v5 sends one Action
# feedback status="departure_ready"; ㉑/㉒ continue while Pinky drives. Same
# name/meaning on Pinky (pinky_camera_drive.camera_straight_drive). False =
# Pinky departs on the final /harvest result as before.
ENABLE_PINKY_DEPARTURE_AFTER_LAST_RISE = True
DIRECT_HOVER_BYPASS_APPROACH_DELTA_GUARD = True

# Pure pre-planning is enabled; feedback/collision-dependent experiments stay
# opt-in until they are verified on the real arm and camera.
ENABLE_ADAPTIVE_ARM_SETTLE = False
ENABLE_PRECOMPUTED_HARVEST_PLANS = True
ENABLE_JOINT_COST_TARGET_ORDER = True
ENABLE_ADAPTIVE_SCAN_SETTLE = False
ENABLE_ADAPTIVE_SCAN_EARLY_EXIT = False
ENABLE_CONTINUOUS_SAFE_APPROACH = False

ARM_SETTLE_MIN_SEC = 0.10
ARM_SETTLE_STABLE_WINDOW_SEC = 0.15
ARM_SETTLE_POSITION_TOLERANCE_DEG = 0.5
ARM_SETTLE_VELOCITY_TOLERANCE_DPS = 0.5

_ORIGINAL_MOVEMENT_DURATION = scan.multi.movement_duration
_direct_hover_pending = False


def reset_direct_hover_state() -> None:
    global _direct_hover_pending
    _direct_hover_pending = False
    v2._precomputed_harvest_plans.clear()


def complete_direct_hover_transition() -> None:
    global _direct_hover_pending
    _direct_hover_pending = False


def should_bypass_direct_hover_approach_delta_guard() -> bool:
    """Bypass only the folded-pose soft guard during a real hover transfer."""
    return bool(
        DIRECT_NEXT_TARGET_FROM_BIN_HOVER
        and DIRECT_HOVER_BYPASS_APPROACH_DELTA_GUARD
        and _direct_hover_pending
    )


def should_use_continuous_safe_approach() -> bool:
    return bool(ENABLE_CONTINUOUS_SAFE_APPROACH)


def settle_after_arm_move(
    arm,
    target_joints,
    max_settle_sec: float,
    cancel_callback=None,
) -> bool:
    """Use feedback settling when enabled, otherwise preserve fixed sleep."""
    if not ENABLE_ADAPTIVE_ARM_SETTLE:
        time.sleep(float(max_settle_sec))
        return False
    return v2.wait_until_arm_settled(
        arm,
        target_joints,
        min_settle_sec=ARM_SETTLE_MIN_SEC,
        max_settle_sec=max_settle_sec,
        position_tolerance_deg=ARM_SETTLE_POSITION_TOLERANCE_DEG,
        velocity_tolerance_dps=ARM_SETTLE_VELOCITY_TOLERANCE_DPS,
        stable_window_sec=ARM_SETTLE_STABLE_WINDOW_SEC,
        cancel_callback=cancel_callback,
    )


def settle_after_scan_move(
    arm,
    target_joints,
    max_settle_sec: float,
    cancel_callback=None,
) -> bool:
    """Settle joint1 before the existing multi-frame observation window."""
    if not ENABLE_ADAPTIVE_SCAN_SETTLE:
        time.sleep(float(max_settle_sec))
        return False
    return v2.wait_until_arm_settled(
        arm,
        target_joints,
        min_settle_sec=ARM_SETTLE_MIN_SEC,
        max_settle_sec=max_settle_sec,
        position_tolerance_deg=ARM_SETTLE_POSITION_TOLERANCE_DEG,
        velocity_tolerance_dps=ARM_SETTLE_VELOCITY_TOLERANCE_DPS,
        stable_window_sec=ARM_SETTLE_STABLE_WINDOW_SEC,
        cancel_callback=cancel_callback,
    )


def prepare_optimized_harvest_targets(
    arm,
    calibration,
    clusters: list[scan.PumpkinCluster],
) -> list[scan.PumpkinCluster]:
    """Pre-validate targets and optionally order by predicted joint time."""
    distance_order = sorted(
        clusters,
        key=lambda cluster: np.hypot(cluster.x, cluster.y),
    )
    if not ENABLE_PRECOMPUTED_HARVEST_PLANS:
        return distance_order

    plans = v2.precompute_harvest_plans(
        arm,
        calibration,
        distance_order,
        bypass_high_delta_guard=DIRECT_NEXT_TARGET_FROM_BIN_HOVER,
    )
    v2._precomputed_harvest_plans = {
        id(plan.cluster): plan for plan in plans
    }
    for index, plan in enumerate(plans, start=1):
        if not plan.valid:
            print(
                f"[수확 사전계획 제외] {index}번: "
                f"{plan.rejection_reason}"
            )
    ordered = v2.order_precomputed_harvest_plans(
        plans,
        optimize_joint_cost=ENABLE_JOINT_COST_TARGET_ORDER,
    )
    print(
        f"[수확 사전계획] {len(plans)}개 목표 중 "
        f"{len(ordered)}개 접근 가능"
    )
    if ENABLE_JOINT_COST_TARGET_ORDER and ordered:
        costs = " → ".join(
            f"#{plan.original_index + 1}({plan.predicted_joint_cost:.2f}초)"
            for plan in ordered
        )
        print("[수확 순서 최적화] 예상 관절시간순을 사용합니다.")
        print(f"[수확 순서] {costs}")
    return [plan.cluster for plan in ordered]


def should_end_scan_early(
    clusters: list[scan.PumpkinCluster],
    target_count: int | None,
) -> bool:
    """Only explicit-count runs may use the disabled-by-default early exit."""
    if not ENABLE_ADAPTIVE_SCAN_EARLY_EXIT or target_count is None:
        return False
    confirmed = [
        cluster
        for cluster in clusters
        if cluster.label() == "ORANGE"
        and len({
            int(round(item.commanded_offset_deg))
            for item in cluster.observations
        }) >= 2
    ]
    return len(confirmed) >= target_count


def recover_direct_hover_for_cleanup(arm) -> bool:
    """Fold from the actual pose before the existing cancel/park cleanup."""
    global _direct_hover_pending
    if not _direct_hover_pending:
        return False
    if v2._BIN_FOLDED_JOINTS is None:
        raise RuntimeError("적재함 방향 접힘 자세가 준비되지 않았습니다.")
    print("[안전 복구] 직행 대기 상공 자세에서 적재함 방향으로 팔을 접습니다.")
    current_joints = np.asarray(arm.joints(), dtype=float)
    arm.move_joints(
        v2._BIN_FOLDED_JOINTS,
        duration=v2.duration_with_safe_speedup(
            current_joints,
            v2._BIN_FOLDED_JOINTS,
            min_duration=BIN_FOLD_DURATION_SEC,
            speedup=NEXT_TARGET_FOLD_SPEEDUP,
        ),
    )
    _direct_hover_pending = False
    return True


def wait_for_manual_departure_signal() -> None:
    """Debug-only manual gate; needs a terminal (stdin), never the server."""
    input(
        "\n[주행 출발 준비] 마지막 호박 적재와 그리퍼 상승이 완료됐습니다. "
        "주행 출발 신호 시점을 확인하려면 Enter: "
    )
    print("[주행 출발 신호] Enter 확인 완료. 로봇팔 정리를 계속합니다.")


def continue_without_departure_signal() -> None:
    """Default with no ROS run: no keyboard, nothing sent (v5 sends ㉔)."""
    print(
        "\n[주행 출발 준비] 마지막 호박 적재와 그리퍼 상승이 완료됐습니다. "
        "자동으로 로봇팔 정리를 계속합니다."
    )


# Fully automatic by default. v5.run_harvest(require_departure_confirmation=
# True) switches to the manual Enter gate for interactive debugging only.
departure_signal_gate = continue_without_departure_signal


def transit_rotation_duration(delta_deg: float) -> float:
    return max(
        MIN_ROTATION_DURATION_SEC,
        float(_ORIGINAL_MOVEMENT_DURATION(delta_deg))
        * TRANSIT_DURATION_FACTOR,
    )


def scan_rotation_duration(delta_deg: float) -> float:
    """Run scan rotations 2.08x faster than the existing transit speed."""
    return (
        float(_ORIGINAL_MOVEMENT_DURATION(delta_deg))
        * SCAN_ROTATION_DURATION_FACTOR
    )


def post_scan_return_rotation_duration(delta_deg: float) -> float:
    """⑧ only: request 2x speed, capped by OMX velocity/acceleration."""
    delta = abs(float(delta_deg))
    requested = scan_rotation_duration(delta) / POST_SCAN_RETURN_SPEEDUP
    velocity_floor = (
        delta * v2.QUINTIC_PEAK_VELOCITY_FACTOR
        / v2.SERVO_PROFILE_VELOCITY_DPS
    )
    acceleration_floor = (
        v2.QUINTIC_PEAK_ACCELERATION_FACTOR * delta
        / v2.SERVO_PROFILE_ACCELERATION_DPS2
    ) ** 0.5
    return max(requested, velocity_floor, acceleration_floor)


def scan_step_rotation_duration(delta_deg: float) -> float:
    """Run moves into scan views 2.704x faster than the transit speed."""
    return (
        float(_ORIGINAL_MOVEMENT_DURATION(delta_deg))
        * SCAN_STEP_DURATION_FACTOR
    )


def scan_target_rotation_duration(
    commanded_deg: float,
    delta_deg: float,
) -> float:
    """Double only the move into the first -140-degree scan view."""
    duration = scan_step_rotation_duration(delta_deg)
    if int(round(float(commanded_deg))) == -140:
        return duration / FIRST_SCAN_ENTRY_SPEED_MULTIPLIER
    return duration


def configure_selective_speed() -> None:
    """Speed up non-descent arm motions; preserve descents and gripper."""
    scan.base.CAMERA_MOVE_DURATION_SEC *= TRANSIT_DURATION_FACTOR

    # 80 mm high approach is a free-space transit motion.
    scan.grasp.HIGH_MOVE_DURATION_SEC *= TRANSIT_DURATION_FACTOR

    # 80 -> 30 -> 10 -> 0 mm pumpkin descent keeps the v3 speed.
    scan.grasp.LOWER_MOVE_DURATION_SEC *= DESCENT_DURATION_FACTOR

    # Base free-space speed; v2 applies the additional held-load 2x factor
    # only after the gripper has closed.
    scan.grasp.LIFT_STEP_DURATION_SEC *= TRANSIT_DURATION_FACTOR
    scan.grasp.RETURN_DURATION_SEC *= TRANSIT_DURATION_FACTOR

    # Keep preparation and folded transport at the existing 1.5x speed.
    scan.multi.movement_duration = transit_rotation_duration

    # Return to centre after the sweep is another 2.08x faster; moves into
    # each scan view use the 2.704x step speed.
    scan.scan_movement_duration = scan_rotation_duration
    scan.post_scan_return_duration = post_scan_return_rotation_duration
    scan.scan_target_movement_duration = scan_target_rotation_duration

    scan.park_arm = park_at_target_speed
    scan.reset_harvest_motion_state = reset_direct_hover_state
    scan.prepare_arm_for_cleanup = recover_direct_hover_for_cleanup
    scan.wait_for_scan_settle = settle_after_scan_move
    scan.prepare_harvest_targets = prepare_optimized_harvest_targets
    scan.should_end_scan_early = should_end_scan_early
    v2.next_target_approach_completed = complete_direct_hover_transition
    v2.direct_hover_approach_delta_guard_bypass_enabled = (
        should_bypass_direct_hover_approach_delta_guard
    )
    v2.continuous_safe_approach_enabled = (
        should_use_continuous_safe_approach
    )


def park_at_target_speed(arm) -> None:
    """㉒: omx_f park() order (gripper, then FOLDED); only the fold is timed."""
    arm.park(
        duration=v2.duration_for_target_joint_speed(
            arm.joints(),
            scan.omx_robot.FOLDED,
            min_duration=PARK_MIN_DURATION_SEC,
        )
    )


def deposit_open_then_rise(
    arm,
    calibration,
    default_gripper_value: float,
    is_last: bool,
) -> None:
    if (
        v2._BIN_HOVER_JOINTS is None
        or v2._BIN_DROP_JOINTS is None
        or v2._BIN_FOLDED_JOINTS is None
    ):
        raise RuntimeError("새 적재함 자세가 준비되지 않았습니다.")

    v2.validate_bin_limits(
        arm,
        ("적재함 상공", v2._BIN_HOVER_JOINTS),
        ("적재함 놓기", v2._BIN_DROP_JOINTS),
        ("적재함 방향 접힘", v2._BIN_FOLDED_JOINTS),
    )

    print("[적재] 호박을 든 채 적재함 상공으로 이동합니다.")
    arm.move_joints(
        v2._BIN_HOVER_JOINTS,
        duration=v2.duration_with_safe_speedup(
            v2._BIN_FOLDED_JOINTS,
            v2._BIN_HOVER_JOINTS,
            min_duration=BIN_HOVER_MIN_DURATION_SEC,
            speedup=v2.HELD_BIN_MOVE_SPEEDUP,
        ),
    )
    settle_after_arm_move(arm, v2._BIN_HOVER_JOINTS, BIN_SETTLE_SEC)

    print("[적재] 새로 저장한 놓기 자세로 하강합니다.")
    arm.move_joints(
        v2._BIN_DROP_JOINTS,
        duration=v2.duration_for_target_joint_speed(
            v2._BIN_HOVER_JOINTS,
            v2._BIN_DROP_JOINTS,
            min_duration=BIN_DESCENT_MIN_DURATION_SEC,
        ),
    )
    settle_after_arm_move(arm, v2._BIN_DROP_JOINTS, BIN_SETTLE_SEC)

    print("[적재] 그리퍼를 열어 주황 호박을 놓습니다.")
    arm.gripper(
        default_gripper_value,
        duration=scan.grasp.GRIPPER_OPEN_DURATION_SEC,
        stall_guard=True,
        wait=True,
    )
    # This wait is for fruit release, not joint settling; keep it fixed.
    time.sleep(BIN_SETTLE_SEC)

    # Keep the gripper open until it has cleared the robot/bin obstacles.
    print("[적재] 열린 그리퍼 그대로 적재함 상공 자세로 먼저 복귀합니다.")
    arm.move_joints(
        v2._BIN_HOVER_JOINTS,
        duration=v2.duration_for_target_joint_speed(
            v2._BIN_DROP_JOINTS,
            v2._BIN_HOVER_JOINTS,
            min_duration=OPEN_GRIPPER_RISE_MIN_DURATION_SEC,
        ),
    )
    settle_after_arm_move(arm, v2._BIN_HOVER_JOINTS, BIN_SETTLE_SEC)

    if not is_last and DIRECT_NEXT_TARGET_FROM_BIN_HOVER:
        global _direct_hover_pending
        _direct_hover_pending = True
        print(
            "[다음 목표 직행] 적재함 상공에서 접힘 자세를 생략하고 "
            "다음 호박으로 이동합니다."
        )
        return

    if is_last:
        # Reached only after ⑱ release, ⑲ open-gripper rise and its settle all
        # returned normally; any failure raised above and skips this.
        departure_signal_gate()
        # Pinky may now be driving away. Everything below stays at the arm's
        # station: gripper width restore in place, then the taught fold from
        # bin hover (base joint unchanged), centre return and ㉒ PARK. The
        # open gripper already cleared the bin at hover, so none of these
        # motions reaches down into the Pinky bin.

    if not is_last:
        print("[다음 목표 준비] 기본 폭을 재확인하고 적재함 방향에서 팔을 접습니다.")

    print("[적재] 상공에서 시작 당시 기본 그리퍼 폭으로 정리합니다.")
    arm.gripper(
        default_gripper_value,
        duration=(
            LAST_PUMPKIN_GRIPPER_RESTORE_DURATION_SEC
            if is_last
            else NEXT_TARGET_GRIPPER_RESTORE_DURATION_SEC
        ),
        stall_guard=False,
        wait=True,
    )

    print("[다음 목표 준비] 적재함 방향에서 팔을 접습니다. (1.5배)")
    arm.move_joints(
        v2._BIN_FOLDED_JOINTS,
        duration=(
            v2.duration_for_target_joint_speed(
                v2._BIN_HOVER_JOINTS,
                v2._BIN_FOLDED_JOINTS,
                min_duration=LAST_PUMPKIN_FOLD_MIN_DURATION_SEC,
            )
            if is_last
            else v2.duration_with_safe_speedup(
                v2._BIN_HOVER_JOINTS,
                v2._BIN_FOLDED_JOINTS,
                min_duration=BIN_FOLD_DURATION_SEC,
                speedup=NEXT_TARGET_FOLD_SPEEDUP,
            )
        ),
    )

    if is_last:
        print("[수확 완료] 마지막 과실이므로 중앙 안전 자세로 복귀합니다.")
        arm.move_joints(
            calibration["camera_joints"],
            duration=LAST_PUMPKIN_CENTER_RETURN_DURATION_SEC,
        )
        settle_after_arm_move(
            arm,
            calibration["camera_joints"],
            LAST_PUMPKIN_CENTER_SETTLE_SEC,
        )
    else:
        print("[다음 목표 준비] 중앙 자세를 거치지 않고 다음 과실로 진행합니다.")


def main() -> None:
    configure_selective_speed()

    # The collision-aware poses were just re-taught.  Use the saved drop pose
    # exactly, without the older v2/v3 additional height interpolation.
    v2.DROP_RAISE_M = 0.0
    (
        v2._BIN_HOVER_JOINTS,
        v2._BIN_DROP_JOINTS,
        saved_drop_m,
    ) = v2.load_adjusted_bin_poses()

    calibration = scan.base.load_calibrations()
    v2._BIN_FOLDED_JOINTS = np.asarray(
        calibration["camera_joints"], dtype=float
    ).copy()
    v2._BIN_FOLDED_JOINTS[0] = v2._BIN_HOVER_JOINTS[0]

    # v2's harvest action looks up the deposit function from its module at
    # runtime, so replace only that stage with the safer ordering above.
    v2.deposit_and_prepare_next = deposit_open_then_rise

    print("새 적재함 자세를 그대로 불러왔습니다:", v2.BIN_POSE_PATH)
    print("적재함 상공 [deg]:", np.round(np.degrees(v2._BIN_HOVER_JOINTS), 1))
    print("적재함 놓기 [deg]:", np.round(np.degrees(v2._BIN_DROP_JOINTS), 1))
    print(f"저장된 상공→놓기 하강량: {saved_drop_m * 1000:.1f} mm")
    print("일반 준비·이동: v3보다 1.5배")
    print("접근·상승·접기·적재함 이동·하강·상승: 관절 평균 21.9°/s 기준")
    print("호박 집기 하강·그리퍼: v3 속도 유지")
    print("호박 배출 후 열린 그리퍼로 상공 복귀한 다음 그리퍼를 정리합니다.")

    scan.require_start = v2.require_full_auto_start
    scan.add_global_track = v2.add_global_track_one_to_one
    scan.print_summary = v2.print_summary_with_requested_names
    scan.harvest_one = v2.harvest_one_direct
    scan.AUTO_COUNTDOWN_SEC = 0
    scan.main()


if __name__ == "__main__":
    main()
