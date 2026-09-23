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
import json
import math
from pathlib import Path
import time

import numpy as np

import pumpkin_auto_scan_count_orange_harvest as scan


BIN_POSE_PATH = Path(__file__).with_name("pumpkin_new_bin_pose.json")
DROP_RAISE_M = 0.005
BIN_HOVER_DURATION_SEC = 8.0
BIN_DROP_DURATION_SEC = 3.0
BIN_FOLD_DURATION_SEC = 8.0
BIN_SETTLE_SEC = 0.7

_BIN_HOVER_JOINTS: np.ndarray | None = None
_BIN_DROP_JOINTS: np.ndarray | None = None
_BIN_FOLDED_JOINTS: np.ndarray | None = None
_ORIGINAL_PRINT_SUMMARY = scan.print_summary


def require_full_auto_start() -> None:
    print("\n이 프로그램은 각도 입력 없이 전 범위를 자동 스캔합니다.")
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


def add_global_track_one_to_one(
    clusters: list[scan.PumpkinCluster],
    track: scan.ViewTrack,
) -> None:
    """Merge across views, never two pumpkins detected in the same view."""
    angle = track_view_angle(track)
    candidates = []
    for cluster in clusters:
        if cluster_has_view_angle(cluster, angle):
            continue
        distance = math.hypot(cluster.x - track.x, cluster.y - track.y)
        if distance <= scan.DUPLICATE_DISTANCE_M:
            candidates.append((distance, cluster))

    if candidates:
        _distance, nearest = min(candidates, key=lambda item: item[0])
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

    for index in (2, 1, 0):
        clearance_mm = scan.grasp.APPROACH_CLEARANCES_M[index] * 1000.0
        print(f"[운반 준비] 집기점 +{clearance_mm:.0f} mm로 상승합니다.")
        arm.move_joints(
            joints_stages[index],
            duration=scan.grasp.LIFT_STEP_DURATION_SEC,
        )

    print("[운반 준비] 과실 방향에서 팔을 접습니다.")
    arm.move_joints(prealign_joints, duration=scan.grasp.RETURN_DURATION_SEC)

    rotation_deg = float(
        np.degrees(_BIN_FOLDED_JOINTS[0] - prealign_joints[0])
    )
    print("[운반] 중앙 기본 각도를 거치지 않고 접힌 상태로 적재함 방향에 이동합니다.")
    arm.move_joints(
        _BIN_FOLDED_JOINTS,
        duration=scan.multi.movement_duration(rotation_deg),
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
    observation = cluster.best_orange()
    if observation is None:
        return False

    target = scan.make_original_height_target(observation.target)
    current_joints = np.asarray(arm.joints(), dtype=float)
    try:
        prealign, prealign_delta, joints_stages, _deltas = (
            scan.multi.plan_fixed_pose_stages_from_folded_pose(
                arm,
                target["xyz_stages"],
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        )
    except (ValueError, RuntimeError) as error:
        print(f"[수확 건너뜀] {harvest_index}번 IK 실패: {error}")
        return False

    print(
        f"\n[주황 호박 자동 수확 {harvest_index}/{harvest_total}] "
        f"XY=({target['world_target_xy'][0]:+.4f}, "
        f"{target['world_target_xy'][1]:+.4f}) m / "
        f"집기 z={target['planned_grasp_z']:+.4f} m"
    )
    print("집기 전 그리퍼를 최대로 열지 않고 기본 폭을 유지합니다.")

    arm.move_joints(
        prealign,
        duration=scan.multi.movement_duration(prealign_delta),
    )
    arm.move_joints(
        joints_stages[0],
        duration=scan.grasp.HIGH_MOVE_DURATION_SEC,
    )
    for index in (1, 2, 3):
        arm.move_joints(
            joints_stages[index],
            duration=scan.grasp.LOWER_MOVE_DURATION_SEC,
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
