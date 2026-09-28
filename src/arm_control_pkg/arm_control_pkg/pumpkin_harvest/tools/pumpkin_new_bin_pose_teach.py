#!/usr/bin/env python3
"""Teach a new two-stage collection-bin pose for the OMX pumpkin harvester.

This program only records poses.  It never opens/closes the gripper and it
does not automatically move to the bin or to park.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from omx_f import OmxFollower


OUTPUT_PATH = Path(__file__).resolve().parent.parent.joinpath("pumpkin_new_bin_pose.json")
JOINT_NAMES = ("joint1", "joint2", "joint3", "joint4", "joint5")
MIN_POSE_DIFFERENCE_DEG = 1.0
LARGE_STAGE_CHANGE_DEG = 45.0


def teach_pose(arm: OmxFollower, label: str, instructions: tuple[str, ...]):
    print(f"\n========== {label} 티칭 ==========")
    for line in instructions:
        print(line)
    print("그리퍼는 이 프로그램에서 작동하지 않습니다.")
    input("팔을 두 손으로 받친 상태에서 Enter를 누르면 토크가 풀립니다: ")

    with arm.teach():
        print("토크가 풀렸습니다. 팔을 계속 받치고 천천히 자세를 맞추세요.")
        input("자세를 정확히 맞춘 뒤 팔을 받친 채 Enter를 누르세요: ")
        joints = np.asarray(arm.joints(), dtype=float).copy()
        pose = np.asarray(arm.pose(), dtype=float).copy()

    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError(f"{label}에서 올바른 5개 관절값을 읽지 못했습니다.")
    if pose.size < 3 or not np.all(np.isfinite(pose[:3])):
        raise ValueError(f"{label}에서 올바른 툴 좌표를 읽지 못했습니다.")

    print("토크가 다시 켜져 현재 자세를 유지합니다.")
    print("관절 [deg]:", np.round(np.degrees(joints), 1))
    print("툴 XYZ [m]:", np.round(pose[:3], 4))
    return joints, pose


def joint_limit_warnings(arm: OmxFollower, joints: np.ndarray, label: str):
    warnings: list[str] = []
    kin = getattr(arm, "kin", None)
    limits = getattr(kin, "joint_limits", {}) if kin is not None else {}
    for name, value in zip(JOINT_NAMES, joints):
        if name not in limits:
            continue
        lo, hi = limits[name]
        if not (float(lo) <= float(value) <= float(hi)):
            warnings.append(
                f"{label} {name}={np.degrees(value):+.1f}도가 "
                f"한계 {np.degrees(lo):+.1f}~{np.degrees(hi):+.1f}도 밖입니다."
            )
    return warnings


def main() -> None:
    arm = None
    try:
        print("새 적재함 자세 티칭 전용 프로그램입니다.")
        print("호박 없이 실행하고, 적재함과 로봇 주변의 장애물을 치우세요.")
        print("자동 이동·그리퍼 동작은 하지 않습니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()

        hover_joints, hover_pose = teach_pose(
            arm,
            "1/2 적재함 상공 자세",
            (
                "그리퍼를 적재함 중앙의 충분히 높은 곳에 놓으세요.",
                "호박을 쥔 상태라고 가정하고 적재함 벽과 충돌하지 않을 여유를 두세요.",
                "이 자세는 수확 위치에서 적재함으로 갈 때 먼저 도착할 안전 자세입니다.",
            ),
        )

        drop_joints, drop_pose = teach_pose(
            arm,
            "2/2 놓기 자세",
            (
                "상공 자세에서 그리퍼를 적재함 안쪽으로 조금만 낮추세요.",
                "그리퍼를 열었을 때 호박이 적재함 안으로 떨어지는 위치로 맞추세요.",
                "그리퍼 끝과 적재함 바닥·벽 사이에는 충분한 간격을 남기세요.",
            ),
        )

        hover_deg = np.degrees(hover_joints)
        drop_deg = np.degrees(drop_joints)
        delta_deg = drop_deg - hover_deg
        max_delta = float(np.max(np.abs(delta_deg)))
        xyz_delta_mm = (drop_pose[:3] - hover_pose[:3]) * 1000.0

        warnings = []
        warnings.extend(joint_limit_warnings(arm, hover_joints, "상공"))
        warnings.extend(joint_limit_warnings(arm, drop_joints, "놓기"))
        if max_delta < MIN_POSE_DIFFERENCE_DEG:
            warnings.append("상공과 놓기 자세가 거의 같습니다.")
        if max_delta > LARGE_STAGE_CHANGE_DEG:
            warnings.append(
                f"상공→놓기 중 한 관절이 {max_delta:.1f}도 변합니다. "
                "두 자세가 가까운 안전 경로인지 다시 확인하세요."
            )
        if float(drop_pose[2]) >= float(hover_pose[2]):
            warnings.append("놓기 자세의 툴 Z가 상공 자세보다 낮지 않습니다.")

        print("\n========== 새 적재함 자세 요약 ==========")
        print("상공 관절 [deg]:", np.round(hover_deg, 1))
        print("놓기 관절 [deg]:", np.round(drop_deg, 1))
        print("관절 변화 [deg]:", np.round(delta_deg, 1))
        print("툴 이동 XYZ [mm]:", np.round(xyz_delta_mm, 1))
        if warnings:
            print("\n주의:")
            for warning in warnings:
                print(f"- {warning}")
        else:
            print("기본 형식·관절 한계 검사를 통과했습니다.")
        print("==========================================")

        answer = input("위 두 자세를 새 파일에 저장하려면 SAVE 입력 (취소 Q): ").strip().upper()
        if answer != "SAVE":
            print("저장하지 않았습니다.")
            return

        data = {
            "schema_version": 1,
            "method": "two_stage_joint_pose_teach",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "joint_names": list(JOINT_NAMES),
            "hover": {
                "joints_rad": hover_joints.tolist(),
                "joints_deg": hover_deg.tolist(),
                "tool_pose": hover_pose.tolist(),
            },
            "drop": {
                "joints_rad": drop_joints.tolist(),
                "joints_deg": drop_deg.tolist(),
                "tool_pose": drop_pose.tolist(),
            },
            "transition": {
                "joint_delta_deg": delta_deg.tolist(),
                "tool_xyz_delta_mm": xyz_delta_mm.tolist(),
                "max_abs_joint_delta_deg": max_delta,
            },
            "warnings_at_save": warnings,
        }
        OUTPUT_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"새 적재함 자세를 저장했습니다: {OUTPUT_PATH}")
        print("자동 이동은 하지 않습니다. 토크가 켜진 현재 자세에서 연결만 종료합니다.")

    finally:
        if arm is not None:
            arm.disconnect()
            print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
