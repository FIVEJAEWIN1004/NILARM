"""Teach and save a safe full-joint pose above the front collection bin."""

import json
from pathlib import Path

import numpy as np

from omx_f import OmxFollower


OUTPUT_PATH = Path(__file__).with_name("pumpkin_bin_pose.json")
FRONT_JOINT1_MAX_DEG = 30.0


def main():
    arm = None

    try:
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("\n적재함 자세를 저장합니다.")
        print("teach 모드에서 팔을 천천히 움직이세요.")
        print("1) joint1을 정면 적재함 방향(0도 부근)으로 맞추기")
        print("2) 팔을 짧고 높게 접어 그리퍼를 적재함 중앙 위에 놓기")
        print("3) 호박이 떨어질 여유 높이를 확보하기")

        with arm.teach():
            input("두 손으로 팔을 받치고 자세를 맞춘 뒤 Enter: ")
            joints = arm.joints().copy()
            pose = arm.pose().copy()

        joints_deg = np.degrees(joints)
        joint1_abs = abs(float(joints_deg[0]))
        print("저장 후보 관절각 [deg]:", np.round(joints_deg, 1))
        print("그리퍼 좌표 [m]:", np.round(pose, 4))

        if joint1_abs > FRONT_JOINT1_MAX_DEG:
            raise ValueError(
                "joint1이 정면 적재함 범위가 아닙니다. "
                f"현재 {joints_deg[0]:.1f}도, 필요 범위는 "
                "-30~+30도입니다. 다시 저장하세요."
            )

        answer = input("이 자세를 적재함 자세로 저장하려면 SAVE 입력: ").strip()
        if answer != "SAVE":
            print("저장하지 않았습니다.")
            return

        data = {
            "bin_joints_rad": [float(value) for value in joints],
            "bin_joints_deg": [float(value) for value in joints_deg],
            "bin_pose_m": [float(value) for value in pose],
        }
        OUTPUT_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"적재함 자세를 저장했습니다: {OUTPUT_PATH}")

    finally:
        if arm is not None:
            try:
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
