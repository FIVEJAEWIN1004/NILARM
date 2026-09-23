#!/usr/bin/env python3
"""Safely validate the newly taught two-stage collection-bin poses.

No pumpkin is held and the gripper is never commanded by this program.
Every robot motion requires an explicit confirmation word.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from omx_f import OmxFollower


POSE_PATH = Path(__file__).resolve().parent.parent.joinpath("pumpkin_new_bin_pose.json")
READY_DURATION_S = 6.0
HOVER_DURATION_S = 8.0
DROP_DURATION_S = 3.0
SETTLE_S = 0.7
JOINT_NAMES = ("joint1", "joint2", "joint3", "joint4", "joint5")


def checked_joints(value, label: str) -> np.ndarray:
    joints = np.asarray(value, dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError(f"{label}에 유효한 5개 관절값이 없습니다.")
    return joints


def load_bin_poses() -> tuple[np.ndarray, np.ndarray, dict]:
    if not POSE_PATH.is_file():
        raise FileNotFoundError(
            f"새 적재함 자세 파일이 없습니다: {POSE_PATH}\n"
            "먼저 pumpkin_new_bin_pose_teach.py에서 SAVE까지 완료하세요."
        )
    data = json.loads(POSE_PATH.read_text(encoding="utf-8"))
    hover = checked_joints(data.get("hover", {}).get("joints_rad"), "hover.joints_rad")
    drop = checked_joints(data.get("drop", {}).get("joints_rad"), "drop.joints_rad")
    return hover, drop, data


def validate_limits(arm: OmxFollower, *poses: tuple[str, np.ndarray]) -> None:
    kin = getattr(arm, "kin", None)
    limits = getattr(kin, "joint_limits", {}) if kin is not None else {}
    for label, joints in poses:
        bad = []
        for name, value in zip(JOINT_NAMES, joints):
            if name in limits:
                lo, hi = limits[name]
                if not (float(lo) <= float(value) <= float(hi)):
                    bad.append(name)
        if bad:
            raise ValueError(f"{label} 자세의 {', '.join(bad)} 관절이 한계 밖입니다.")


def require(command: str, description: str) -> bool:
    answer = input(f"{description}\n진행하려면 {command} 입력 (중단 Q): ").strip().upper()
    if answer == "Q":
        print("사용자가 검증을 중단했습니다. 추가 이동은 하지 않습니다.")
        return False
    if answer != command:
        print(f"'{command}'가 입력되지 않아 추가 이동을 중단합니다.")
        return False
    return True


def show_pose(label: str, joints: np.ndarray) -> None:
    print(f"{label} 관절 [deg]:", np.round(np.degrees(joints), 1))


def main() -> None:
    hover_joints, drop_joints, data = load_bin_poses()
    transition = data.get("transition", {})

    print("새 적재함 빈 그리퍼 이동 검증입니다.")
    print("호박을 잡지 말고 적재함을 티칭 당시 위치에 고정하세요.")
    print("그리퍼는 열거나 닫지 않습니다.")
    show_pose("상공", hover_joints)
    show_pose("놓기", drop_joints)
    if "tool_xyz_delta_mm" in transition:
        print("저장된 툴 이동 XYZ [mm]:", np.round(transition["tool_xyz_delta_mm"], 1))

    arm = None
    try:
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        validate_limits(arm, ("상공", hover_joints), ("놓기", drop_joints))

        current = np.asarray(arm.joints(), dtype=float)
        show_pose("현재", current)

        if not require(
            "MOVE_READY",
            "사람·케이블·적재함 주변을 확인했습니다. 먼저 기본 안전 자세로 이동합니다.",
        ):
            return
        arm.ready(duration=READY_DURATION_S)
        time.sleep(SETTLE_S)
        print("기본 안전 자세에 도착했습니다.")

        if not require(
            "MOVE_HOVER",
            "기본 자세에서 새 적재함 상공 자세로 천천히 이동합니다.",
        ):
            return
        arm.move_joints(hover_joints, duration=HOVER_DURATION_S)
        time.sleep(SETTLE_S)
        print("적재함 상공에 도착했습니다. 벽·케이블·카메라 간섭을 확인하세요.")

        if not require(
            "MOVE_DROP",
            "간섭이 없으면 빈 그리퍼를 저장된 놓기 자세까지 39 mm가량 낮춥니다.",
        ):
            return
        arm.move_joints(drop_joints, duration=DROP_DURATION_S)
        time.sleep(SETTLE_S)
        print("놓기 자세에 도착했습니다. 그리퍼는 작동하지 않았습니다.")
        print("그리퍼가 적재함 바닥·벽에 닿지 않고 호박을 놓기 좋은지 확인하세요.")

        if not require(
            "RETURN_HOVER",
            "확인이 끝났으면 같은 경로로 적재함 상공 자세에 복귀합니다.",
        ):
            return
        arm.move_joints(hover_joints, duration=DROP_DURATION_S)
        time.sleep(SETTLE_S)
        print("적재함 상공 자세로 복귀했습니다.")

        if not require(
            "RETURN_READY",
            "마지막으로 기본 안전 자세로 복귀합니다.",
        ):
            return
        arm.ready(duration=HOVER_DURATION_S)
        time.sleep(SETTLE_S)
        print("새 적재함 빈 그리퍼 경로 검증이 끝났습니다.")

    finally:
        if arm is not None:
            arm.disconnect()
            print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
