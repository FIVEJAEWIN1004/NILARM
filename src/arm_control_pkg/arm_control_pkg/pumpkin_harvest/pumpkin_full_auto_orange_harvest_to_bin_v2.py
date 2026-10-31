#!/usr/bin/env python3
"""Improved full-auto orange pumpkin harvest-to-bin pipeline.

Changes from v1:
- release 5 mm above the taught drop pose;
- print exact Orange/Green totals before harvesting;
- prevent two tracks from the same camera angle merging into one pumpkin;
- move bin -> next target directly through a folded transport pose, without
  returning to the central camera angle between pumpkins.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

import numpy as np

from vision_pkg.pumpkin_detection import spatial_tracking

from . import joint_trajectory
from . import pumpkin_auto_scan_count_orange_harvest as scan


BIN_POSE_PATH = Path(__file__).with_name("pumpkin_new_bin_pose.json")
DROP_RAISE_M = 0.005
BIN_HOVER_DURATION_SEC = 8.0
BIN_DROP_DURATION_SEC = 3.0
BIN_FOLD_DURATION_SEC = 8.0
BIN_SETTLE_SEC = 0.7
# The normal scan step (③) averages 22.53 deg/s.  21.9 deg/s keeps the
# quintic peak (x1.875 = 41.06 deg/s) under the ~41.2 deg/s servo Profile
# Velocity.  Each floor keeps short moves gentle; held moves are stricter.
TARGET_AVERAGE_JOINT_SPEED_DPS = 21.9
SERVO_PROFILE_VELOCITY_DPS = 41.2
SERVO_PROFILE_ACCELERATION_DPS2 = 215.0
QUINTIC_PEAK_VELOCITY_FACTOR = 1.875
QUINTIC_PEAK_ACCELERATION_FACTOR = 5.7735
SAFE_APPROACH_SPEEDUP = 1.3
HELD_BIN_MOVE_SPEEDUP = 1.3
SAFE_APPROACH_PREALIGN_MIN_DURATION_SEC = 1.2
SAFE_APPROACH_HIGH_MIN_DURATION_SEC = 1.4
LIFT_STEP_MIN_DURATION_SEC = 0.8
LIFT_EARLY_SPEEDUP = 1.7
LIFT_EARLY_MIN_DURATION_SEC = 0.50
HELD_FOLD_MIN_DURATION_SEC = 1.4
HELD_BIN_ROTATION_MIN_DURATION_SEC = 1.5
FINAL_APPROACH_DURATIONS_SEC = (2.5, 2.0, 2.0)
# The lift passes +10/+30 mm without stopping; at +80 mm only joints that
# keep their direction into the fold continue, at no more than this speed.
LIFT_TO_FOLD_VIA_SPEED_DPS = 5.0

_BIN_HOVER_JOINTS: np.ndarray | None = None
_BIN_DROP_JOINTS: np.ndarray | None = None
_BIN_FOLDED_JOINTS: np.ndarray | None = None
_ORIGINAL_PRINT_SUMMARY = scan.print_summary
_precomputed_harvest_plans: dict[int, "HarvestPlan"] = {}


def next_target_approach_completed() -> None:
    """Notify an optional wrapper after the next pre-alignment completes."""


def direct_hover_approach_delta_guard_bypass_enabled() -> bool:
    """Keep the normal folded-pose approach guards unless v4 opts in."""
    return False


def continuous_safe_approach_enabled() -> bool:
    """Keep the verified stop-to-stop approach unless v4 opts in."""
    return False


@dataclass
class HarvestPlan:
    """Pre-harvest feasibility and estimated approach cost for one cluster."""

    cluster: scan.PumpkinCluster
    observation: scan.Detection | None
    corrected_target: dict | None
    prealign_joints: np.ndarray | None
    joints_stages: list[np.ndarray] | None
    approach_deltas: list | None
    predicted_approach_duration: float
    predicted_joint_cost: float
    valid: bool
    rejection_reason: str = ""
    original_index: int = 0


def wait_until_arm_settled(
    arm,
    target_joints,
    *,
    min_settle_sec: float,
    max_settle_sec: float,
    position_tolerance_deg: float = 0.5,
    velocity_tolerance_dps: float = 0.5,
    stable_window_sec: float = 0.15,
    sample_period_sec: float = 0.05,
    cancel_callback=None,
) -> bool:
    """Return early on stable feedback, falling back to the original timeout."""
    started = time.monotonic()
    deadline = started + float(max_settle_sec)
    target = np.asarray(target_joints, dtype=float)
    previous = None
    previous_time = None
    stable_since = None

    while True:
        if cancel_callback is not None and cancel_callback():
            raise scan.ScanCancelled
        now = time.monotonic()
        remaining = deadline - now
        if remaining <= 0.0:
            return False
        time.sleep(min(float(sample_period_sec), remaining))
        now = time.monotonic()
        try:
            current = np.asarray(arm.joints(), dtype=float)
            if current.shape != target.shape or not np.all(np.isfinite(current)):
                raise ValueError("invalid joint feedback")
        except (AttributeError, TypeError, ValueError, RuntimeError):
            remaining = deadline - now
            if remaining > 0.0:
                time.sleep(remaining)
            return False

        if previous is None:
            velocity = np.inf
        else:
            dt = max(now - float(previous_time), 1e-6)
            velocity = float(
                np.max(np.abs(np.degrees(current - previous))) / dt
            )
        position_error = float(
            np.max(np.abs(np.degrees(current - target)))
        )
        elapsed = now - started
        stable = (
            elapsed >= float(min_settle_sec)
            and position_error <= float(position_tolerance_deg)
            and velocity <= float(velocity_tolerance_dps)
        )
        if stable:
            if stable_since is None:
                stable_since = now
            if now - stable_since >= float(stable_window_sec):
                return True
        else:
            stable_since = None
        previous = current
        previous_time = now


def duration_for_target_joint_speed(
    start_joints,
    target_joints,
    *,
    min_duration: float,
    target_speed_dps: float = TARGET_AVERAGE_JOINT_SPEED_DPS,
) -> float:
    """Time a joint move [rad] so its largest joint averages <= target speed."""
    delta = np.asarray(target_joints, dtype=float) - np.asarray(
        start_joints, dtype=float
    )
    max_delta_deg = float(np.max(np.abs(np.degrees(delta))))
    return max(float(min_duration), max_delta_deg / target_speed_dps)


def duration_with_safe_speedup(
    start_joints,
    target_joints,
    *,
    min_duration: float,
    speedup: float,
) -> float:
    """Shorten a move by the requested factor within OMX profile limits."""
    delta = np.asarray(target_joints, dtype=float) - np.asarray(
        start_joints, dtype=float
    )
    max_delta_deg = float(np.max(np.abs(np.degrees(delta))))
    current = duration_for_target_joint_speed(
        start_joints,
        target_joints,
        min_duration=min_duration,
    )
    velocity_floor = (
        max_delta_deg * QUINTIC_PEAK_VELOCITY_FACTOR
        / SERVO_PROFILE_VELOCITY_DPS
    )
    acceleration_floor = (
        QUINTIC_PEAK_ACCELERATION_FACTOR * max_delta_deg
        / SERVO_PROFILE_ACCELERATION_DPS2
    ) ** 0.5
    return max(current / float(speedup), velocity_floor, acceleration_floor)


def early_lift_duration(start_joints, target_joints) -> float:
    """Speed up only the first two lift segments, with a final 0.50 s floor."""
    return max(
        LIFT_EARLY_MIN_DURATION_SEC,
        duration_with_safe_speedup(
            start_joints,
            target_joints,
            min_duration=LIFT_STEP_MIN_DURATION_SEC,
            speedup=LIFT_EARLY_SPEEDUP,
        ),
    )


def require_full_auto_start() -> None:
    angles = ", ".join(f"{angle:+d}" for angle in scan.SCAN_OFFSETS_DEG)
    print("\n이 프로그램은 각도 입력 없이 대회용 선택 각도를 자동 스캔합니다.")
    print(f"자동 스캔 각도: {angles}도")
    print("전체 호박을 중복 제거해 집계한 뒤 주황 호박만 자동 수확합니다.")
    print("초록·UNKNOWN 호박에는 접근하지 않습니다.")
    print("사람·케이블을 치우고 적재함을 티칭·검증한 위치에 고정하세요.")
    while True:
        answer = input("자동 스캔을 시작하려면 HARVEST_ORANGE 입력: ").strip()
        if answer == "HARVEST_ORANGE":
            return
        if answer.upper() == "Q":
            raise scan.ScanCancelled
        print("HARVEST_ORANGE를 정확히 입력해야 시작합니다. 취소는 Q입니다.")


def checked_vector(value, size: int, label: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (size,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{label}에 유효한 {size}개 값이 없습니다.")
    return vector


def load_adjusted_bin_poses() -> tuple[np.ndarray, np.ndarray, float]:
    """Return hover and a joint-interpolated drop pose about 5 mm higher."""
    if not BIN_POSE_PATH.is_file():
        raise FileNotFoundError(
            f"새 적재함 자세 파일이 없습니다: {BIN_POSE_PATH}\n"
            "먼저 pumpkin_new_bin_pose_teach.py에서 SAVE까지 완료하세요."
        )

    data = json.loads(BIN_POSE_PATH.read_text(encoding="utf-8"))
    hover_data = data.get("hover", {})
    drop_data = data.get("drop", {})
    hover_joints = checked_vector(hover_data.get("joints_rad"), 5, "hover.joints_rad")
    taught_drop_joints = checked_vector(drop_data.get("joints_rad"), 5, "drop.joints_rad")

    hover_pose = np.asarray(hover_data.get("tool_pose"), dtype=float)
    drop_pose = np.asarray(drop_data.get("tool_pose"), dtype=float)
    if (
        hover_pose.size < 3
        or drop_pose.size < 3
        or not np.all(np.isfinite(hover_pose[:3]))
        or not np.all(np.isfinite(drop_pose[:3]))
    ):
        raise ValueError("적재함 JSON에 상공·놓기 tool_pose가 없습니다.")

    taught_drop_m = float(hover_pose[2] - drop_pose[2])
    if taught_drop_m <= DROP_RAISE_M:
        raise ValueError(
            f"저장된 하강량이 {taught_drop_m * 1000:.1f}mm라서 "
            f"{DROP_RAISE_M * 1000:.1f}mm 높일 수 없습니다."
        )

    adjusted_drop_m = taught_drop_m - DROP_RAISE_M
    interpolation = adjusted_drop_m / taught_drop_m
    adjusted_drop_joints = hover_joints + interpolation * (
        taught_drop_joints - hover_joints
    )
    return hover_joints, adjusted_drop_joints, adjusted_drop_m


def track_view_angle(track: scan.ViewTrack) -> int:
    return int(round(track.best_detection().commanded_offset_deg))


def cluster_has_view_angle(cluster: scan.PumpkinCluster, angle: int) -> bool:
    return any(
        int(round(observation.commanded_offset_deg)) == angle
        for observation in cluster.observations
    )


# Positive Z is upward.  These competition-only residuals adjust the complete
# approach stack and final grasp height for the selected observation angle.
ANGLE_GRASP_Z_OFFSET_M = {
    -140: -0.025,  # 25 mm farther down (raised 5 mm)
    70: 0.005,    # 5 mm less down
    130: -0.018,  # 18 mm farther down (raised 2 mm)
}


def apply_angle_grasp_z_offset(target: dict, commanded_offset_deg: float) -> dict:
    """Return a copied target with the verified per-angle grasp-Z residual."""
    angle = int(round(float(commanded_offset_deg)))
    z_offset = ANGLE_GRASP_Z_OFFSET_M.get(angle, 0.0)
    result = dict(target)
    result["angle_grasp_z_offset_m"] = z_offset
    result["planned_grasp_z"] = float(target["planned_grasp_z"]) + z_offset
    result["xyz_stages"] = [
        np.asarray(stage, dtype=float).copy() for stage in target["xyz_stages"]
    ]
    for stage in result["xyz_stages"]:
        stage[2] += z_offset
    return result


def select_grasp_z_correction_angle(
    cluster: scan.PumpkinCluster,
    selected_angle: int,
) -> int:
    """Use a unique calibrated view even when another view supplies XY."""
    observed_angles = {
        int(round(item.commanded_offset_deg)) for item in cluster.observations
    }
    calibrated_observations = observed_angles.intersection(
        ANGLE_GRASP_Z_OFFSET_M
    )
    if len(calibrated_observations) == 1:
        return calibrated_observations.pop()
    return selected_angle


def corrected_target_for_cluster(
    cluster: scan.PumpkinCluster,
) -> tuple[scan.Detection, dict, int]:
    """Build the same corrected target used by the real harvest path."""
    observation = cluster.best_orange()
    if observation is None:
        raise ValueError("수확 가능한 주황 관측이 없습니다.")
    selected_angle = int(round(observation.commanded_offset_deg))
    correction_angle = select_grasp_z_correction_angle(
        cluster,
        selected_angle,
    )
    target = scan.make_original_height_target(observation.target)
    target = apply_angle_grasp_z_offset(target, correction_angle)
    return observation, target, correction_angle


def solve_harvest_approach(
    arm,
    calibration,
    cluster: scan.PumpkinCluster,
    current_joints,
    *,
    bypass_high_delta_guard: bool,
):
    """Reuse production corrections and IK for pre-plan and live re-plan."""
    observation, target, correction_angle = corrected_target_for_cluster(
        cluster
    )
    prealign, prealign_delta, joints_stages, deltas = (
        scan.multi.plan_fixed_pose_stages_from_folded_pose(
            arm,
            target["xyz_stages"],
            np.asarray(current_joints, dtype=float),
            calibration["pitch_rad"],
            calibration["roll_rad"],
            bypass_high_delta_guard=bypass_high_delta_guard,
        )
    )
    prealign_duration = duration_with_safe_speedup(
        current_joints,
        prealign,
        min_duration=SAFE_APPROACH_PREALIGN_MIN_DURATION_SEC,
        speedup=SAFE_APPROACH_SPEEDUP,
    )
    high_duration = duration_with_safe_speedup(
        prealign,
        joints_stages[0],
        min_duration=SAFE_APPROACH_HIGH_MIN_DURATION_SEC,
        speedup=SAFE_APPROACH_SPEEDUP,
    )
    return (
        observation,
        target,
        correction_angle,
        prealign,
        prealign_delta,
        joints_stages,
        deltas,
        prealign_duration,
        high_duration,
    )


def precompute_harvest_plans(
    arm,
    calibration,
    clusters: list[scan.PumpkinCluster],
    *,
    bypass_high_delta_guard: bool,
) -> list[HarvestPlan]:
    """Validate every target before motion and estimate its approach cost."""
    current_joints = np.asarray(arm.joints(), dtype=float)
    plans = []
    for original_index, cluster in enumerate(clusters):
        try:
            (
                observation,
                target,
                _correction_angle,
                prealign,
                _prealign_delta,
                joints_stages,
                deltas,
                prealign_duration,
                high_duration,
            ) = solve_harvest_approach(
                arm,
                calibration,
                cluster,
                current_joints,
                bypass_high_delta_guard=bypass_high_delta_guard,
            )
            plans.append(HarvestPlan(
                cluster=cluster,
                observation=observation,
                corrected_target=target,
                prealign_joints=prealign,
                joints_stages=joints_stages,
                approach_deltas=deltas,
                predicted_approach_duration=(
                    prealign_duration + high_duration
                ),
                predicted_joint_cost=prealign_duration + high_duration,
                valid=True,
                original_index=original_index,
            ))
        except (ValueError, RuntimeError) as error:
            plans.append(HarvestPlan(
                cluster=cluster,
                observation=cluster.best_orange(),
                corrected_target=None,
                prealign_joints=None,
                joints_stages=None,
                approach_deltas=None,
                predicted_approach_duration=float("inf"),
                predicted_joint_cost=float("inf"),
                valid=False,
                rejection_reason=str(error),
                original_index=original_index,
            ))
    return plans


def order_precomputed_harvest_plans(
    plans: list[HarvestPlan],
    *,
    optimize_joint_cost: bool,
) -> list[HarvestPlan]:
    """Return feasible plans deterministically, optionally by motion cost."""
    valid = [plan for plan in plans if plan.valid]
    if optimize_joint_cost:
        valid.sort(key=lambda plan: (
            plan.predicted_joint_cost,
            math.hypot(plan.cluster.x, plan.cluster.y),
            plan.original_index,
        ))
    else:
        valid.sort(key=lambda plan: (
            math.hypot(plan.cluster.x, plan.cluster.y),
            plan.original_index,
        ))
    return valid


def add_global_track_one_to_one(
    clusters: list[scan.PumpkinCluster],
    track: scan.ViewTrack,
) -> None:
    """Merge across views, never two pumpkins detected in the same view."""
    angle = track_view_angle(track)
    nearest = spatial_tracking.nearest_within(
        clusters,
        (track.x, track.y),
        scan.DUPLICATE_DISTANCE_M,
        eligible=lambda cluster: not cluster_has_view_angle(cluster, angle),
    )
    if nearest is not None:
        nearest.add_view(track)
        return

    clusters.append(
        scan.PumpkinCluster(
            x=track.x,
            y=track.y,
            observations=[track.best_detection()],
        )
    )


def print_summary_with_requested_names(
    clusters: list[scan.PumpkinCluster],
) -> list[scan.PumpkinCluster]:
    ripe = _ORIGINAL_PRINT_SUMMARY(clusters)
    counts = Counter(cluster.label() for cluster in clusters)
    print("\n========== Pumpkin Count ==========")
    print(f"Orange Pumpkin - {counts['ORANGE']}")
    print(f"Green Pumpkin - {counts['GREEN']}")
    if counts["UNKNOWN"]:
        print(f"Unknown Pumpkin - {counts['UNKNOWN']}")
    print("===================================")
    if ripe:
        input(
            "로봇팔이 중앙 기본 자세에 있습니다. 주변을 확인한 뒤 "
            "익은 과실 수확을 시작하려면 Enter: "
        )
    return ripe


def validate_bin_limits(arm, *poses: tuple[str, np.ndarray]) -> None:
    joint_names = ("joint1", "joint2", "joint3", "joint4", "joint5")
    kin = getattr(arm, "kin", None)
    limits = getattr(kin, "joint_limits", {}) if kin is not None else {}
    for label, joints in poses:
        bad = []
        for name, value in zip(joint_names, joints):
            if name in limits:
                lo, hi = limits[name]
                if not (float(lo) <= float(value) <= float(hi)):
                    bad.append(name)
        if bad:
            raise ValueError(f"{label} 자세의 {', '.join(bad)} 관절이 한계 밖입니다.")


def move_held_pumpkin_to_bin(
    arm,
    prealign_joints: np.ndarray,
    joints_stages: list[np.ndarray],
) -> None:
    """Lift, fold at the fruit angle, then rotate directly to the bin angle."""
    if _BIN_FOLDED_JOINTS is None:
        raise RuntimeError("적재함 운반 자세가 준비되지 않았습니다.")

    # Time the first lift step from where the arm really is, as move_joints does.
    lift_path = [np.asarray(arm.joints(), dtype=float)] + [
        joints_stages[index] for index in (2, 1, 0)
    ]
    segments = []
    for index, (start, target) in enumerate(
        zip(lift_path, lift_path[1:])
    ):
        if index < 2:
            duration = early_lift_duration(start, target)
        else:
            duration = duration_for_target_joint_speed(
                start,
                target,
                min_duration=LIFT_STEP_MIN_DURATION_SEC,
            )
        segments.append((target, duration))
    segments.append((
        prealign_joints,
        duration_with_safe_speedup(
            joints_stages[0],
            prealign_joints,
            min_duration=HELD_FOLD_MIN_DURATION_SEC,
            speedup=HELD_BIN_MOVE_SPEEDUP,
        ),
    ))
    print("[운반 준비] +10/+30 mm를 멈추지 않고 지나 +80 mm까지 상승한 뒤 팔을 접습니다.")
    joint_trajectory.move_joints_continuous(
        arm,
        segments,
        via_speed_caps_dps=(
            TARGET_AVERAGE_JOINT_SPEED_DPS,
            TARGET_AVERAGE_JOINT_SPEED_DPS,
            LIFT_TO_FOLD_VIA_SPEED_DPS,
        ),
    )

    print("[운반] 중앙 기본 각도를 거치지 않고 접힌 상태로 적재함 방향에 이동합니다.")
    arm.move_joints(
        _BIN_FOLDED_JOINTS,
        duration=duration_with_safe_speedup(
            prealign_joints,
            _BIN_FOLDED_JOINTS,
            min_duration=HELD_BIN_ROTATION_MIN_DURATION_SEC,
            speedup=HELD_BIN_MOVE_SPEEDUP,
        ),
    )


def deposit_and_prepare_next(
    arm,
    calibration,
    default_gripper_value: float,
    is_last: bool,
) -> None:
    if (
        _BIN_HOVER_JOINTS is None
        or _BIN_DROP_JOINTS is None
        or _BIN_FOLDED_JOINTS is None
    ):
        raise RuntimeError("새 적재함 자세가 준비되지 않았습니다.")

    validate_bin_limits(
        arm,
        ("적재함 상공", _BIN_HOVER_JOINTS),
        ("5mm 상향 놓기", _BIN_DROP_JOINTS),
        ("적재함 방향 접힘", _BIN_FOLDED_JOINTS),
    )

    print("[적재] 새 적재함 상공 자세로 이동합니다.")
    arm.move_joints(_BIN_HOVER_JOINTS, duration=BIN_HOVER_DURATION_SEC)
    time.sleep(BIN_SETTLE_SEC)

    print("[적재] 기존 놓기 위치보다 약 5mm 높은 자세로 하강합니다.")
    arm.move_joints(_BIN_DROP_JOINTS, duration=BIN_DROP_DURATION_SEC)
    time.sleep(BIN_SETTLE_SEC)

    print("[적재] 그리퍼를 열어 주황 호박을 놓습니다.")
    arm.open_gripper(
        duration=scan.grasp.GRIPPER_OPEN_DURATION_SEC,
        stall_guard=True,
        wait=True,
    )
    time.sleep(BIN_SETTLE_SEC)

    print("[적재] 시작 당시 기본 그리퍼 폭으로 복원합니다.")
    arm.gripper(
        default_gripper_value,
        duration=scan.RESTORE_GRIPPER_DURATION_SEC,
        stall_guard=False,
        wait=True,
    )

    print("[적재] 적재함 상공 자세로 복귀합니다.")
    arm.move_joints(_BIN_HOVER_JOINTS, duration=BIN_DROP_DURATION_SEC)
    time.sleep(BIN_SETTLE_SEC)

    print("[다음 목표 준비] 적재함 방향에서 팔을 접습니다.")
    arm.move_joints(_BIN_FOLDED_JOINTS, duration=BIN_FOLD_DURATION_SEC)

    if is_last:
        rotation_deg = float(
            np.degrees(
                calibration["camera_joints"][0] - _BIN_FOLDED_JOINTS[0]
            )
        )
        print("[수확 완료] 마지막 과실이므로 중앙 안전 자세로 복귀합니다.")
        arm.move_joints(
            calibration["camera_joints"],
            duration=scan.multi.movement_duration(rotation_deg),
        )
        time.sleep(scan.base.SETTLE_TIME_SEC)
    else:
        print("[다음 목표 준비] 중앙 자세로 돌아가지 않고 다음 과실로 진행합니다.")


def harvest_one_direct(
    arm,
    calibration,
    cluster: scan.PumpkinCluster,
    default_gripper_value: float,
    harvest_index: int,
    harvest_total: int,
):
    current_joints = np.asarray(arm.joints(), dtype=float)
    bypass_high_delta_guard = bool(
        direct_hover_approach_delta_guard_bypass_enabled()
    )
    try:
        (
            observation,
            target,
            z_correction_angle,
            prealign,
            _prealign_delta,
            joints_stages,
            _deltas,
            prealign_duration,
            high_approach_duration,
        ) = solve_harvest_approach(
            arm,
            calibration,
            cluster,
            current_joints,
            bypass_high_delta_guard=bypass_high_delta_guard,
        )
    except (ValueError, RuntimeError) as error:
        print(f"[수확 건너뜀] {harvest_index}번 IK 실패: {error}")
        return False

    observed_angles = sorted(
        {int(round(item.commanded_offset_deg)) for item in cluster.observations}
    )
    selected_angle = int(round(observation.commanded_offset_deg))

    print(
        f"\n[주황 호박 자동 수확 {harvest_index}/{harvest_total}] "
        f"XY=({target['world_target_xy'][0]:+.4f}, "
        f"{target['world_target_xy'][1]:+.4f}) m / "
        f"집기 z={target['planned_grasp_z']:+.4f} m"
    )
    z_offset_mm = target["angle_grasp_z_offset_m"] * 1000.0
    print(
        f"[각도별 높이 보정] 관측각={observed_angles}, "
        f"XY 선택각={selected_angle:+d}도, "
        f"높이 보정각={z_correction_angle:+d}도, Z={z_offset_mm:+.1f} mm"
    )
    print("집기 전 그리퍼를 최대로 열지 않고 기본 폭을 유지합니다.")

    if bypass_high_delta_guard:
        # Keep a 10 ms safety margin above a profile-limit floor instead of
        # rounding a calculated 3.463... seconds down in the command/log.
        high_approach_duration = (
            np.ceil(high_approach_duration * 100.0) / 100.0
        )
        max_delta_deg = float(
            np.max(np.abs(np.degrees(joints_stages[0] - prealign)))
        )
        print(
            "[직행 접근] 상공 직행 모드이므로 +80mm 접근 변화량 "
            "소프트 제한을 생략합니다."
        )
        print(
            f"[직행 접근] 최대 관절 변화 {max_delta_deg:.1f}도, "
            f"안전 duration {high_approach_duration:.2f}초"
        )

    if continuous_safe_approach_enabled():
        try:
            joint_trajectory.move_joints_continuous(
                arm,
                (
                    (prealign, prealign_duration),
                    (joints_stages[0], high_approach_duration),
                ),
                via_speed_caps_dps=(0.0,),
            )
            next_target_approach_completed()
            print("[연속 접근] prealign과 +80mm waypoint 검증 경로를 완료했습니다.")
        except ValueError as error:
            print(f"[연속 접근 fallback] {error}; 기존 정지형 접근을 사용합니다.")
            arm.move_joints(prealign, duration=prealign_duration)
            next_target_approach_completed()
            arm.move_joints(
                joints_stages[0],
                duration=high_approach_duration,
            )
    else:
        arm.move_joints(prealign, duration=prealign_duration)
        next_target_approach_completed()
        arm.move_joints(
            joints_stages[0],
            duration=high_approach_duration,
        )
    for index, duration in zip(
        (1, 2, 3),
        FINAL_APPROACH_DURATIONS_SEC,
    ):
        arm.move_joints(
            joints_stages[index],
            duration=duration,
        )

    print("[집기] 전류 제한을 사용해 그리퍼를 닫습니다.")
    arm.close_gripper(
        duration=scan.grasp.GRIPPER_CLOSE_DURATION_SEC,
        stall_guard=True,
        wait=True,
    )

    holding = True
    try:
        move_held_pumpkin_to_bin(arm, prealign, joints_stages)
        deposit_and_prepare_next(
            arm,
            calibration,
            default_gripper_value,
            is_last=(harvest_index == harvest_total),
        )
        holding = False
    except Exception:
        if holding:
            print("\n[중요] 오류 시점에 그리퍼가 호박을 잡고 있을 수 있습니다.")
            print("자동으로 그리퍼를 열거나 정리 자세로 이동하지 않습니다.")
            print("호박과 로봇팔을 직접 받친 뒤 상태를 확인하세요.")
        raise

    print(f"[완료] {harvest_index}번 주황 호박을 새 적재함에 넣었습니다.")
    return True


def main() -> None:
    global _BIN_HOVER_JOINTS, _BIN_DROP_JOINTS, _BIN_FOLDED_JOINTS

    (
        _BIN_HOVER_JOINTS,
        _BIN_DROP_JOINTS,
        adjusted_drop_m,
    ) = load_adjusted_bin_poses()

    # A folded transport posture at the bin's joint1 angle.  The remaining
    # joints are filled after the normal calibration is loaded inside scan.main;
    # use the saved camera calibration here through the same loader.
    calibration = scan.base.load_calibrations()
    _BIN_FOLDED_JOINTS = np.asarray(
        calibration["camera_joints"], dtype=float
    ).copy()
    _BIN_FOLDED_JOINTS[0] = _BIN_HOVER_JOINTS[0]

    print("새 적재함 자세를 불러왔습니다:", BIN_POSE_PATH)
    print("적재함 상공 [deg]:", np.round(np.degrees(_BIN_HOVER_JOINTS), 1))
    print("5mm 상향 놓기 [deg]:", np.round(np.degrees(_BIN_DROP_JOINTS), 1))
    print(f"조정된 예상 하강량: {adjusted_drop_m * 1000:.1f} mm")
    print("과실 사이에는 중앙 기본 각도를 거치지 않는 접힘 운반 경로를 사용합니다.")

    scan.require_start = require_full_auto_start
    scan.add_global_track = add_global_track_one_to_one
    scan.print_summary = print_summary_with_requested_names
    scan.harvest_one = harvest_one_direct
    scan.AUTO_COUNTDOWN_SEC = 0
    scan.main()


if __name__ == "__main__":
    main()
