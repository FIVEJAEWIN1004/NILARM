"""Teach the -90-degree view and derive the mirrored +90-degree view.

The arm first moves to joint1=-90 degrees. The user adjusts the camera posture
once while watching the live video and presses S. That complete five-joint pose
is saved as zone B. Zone A is generated from the same pose by changing only the
sign of joint1; joints 2-5 remain identical. Press Q to cancel safely.
"""

import json
import time
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


PLANE_CALIBRATION_PATH = Path(__file__).with_name(
    "pumpkin_plane_calibration.json"
)
OUTPUT_PATH = Path(__file__).with_name("pumpkin_ab_view_poses.json")

B_INITIAL_JOINT1_DEG = -90.0
MOVE_DURATION_SEC = 8.0
SETTLE_TIME_SEC = 0.7


def load_camera_settings():
    if not PLANE_CALIBRATION_PATH.is_file():
        raise FileNotFoundError(
            f"기존 보정 파일이 없습니다: {PLANE_CALIBRATION_PATH}"
        )

    data = json.loads(PLANE_CALIBRATION_PATH.read_text(encoding="utf-8"))
    camera = data["camera"]
    joints = np.asarray(data["camera_pose"]["joints_rad"], dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError("camera_pose.joints_rad 값이 올바르지 않습니다.")

    return {
        "index": int(camera["index"]),
        "width": int(camera["width"]),
        "height": int(camera["height"]),
        "base_joints": joints,
    }


def open_camera(settings):
    cap = cv2.VideoCapture(settings["index"], cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        raise RuntimeError(f"카메라 /dev/video{settings['index']}를 열 수 없습니다.")
    for _ in range(8):
        cap.read()
    return cap


def move_to_initial_view(arm, base_joints, joint1_deg, zone):
    target = base_joints.copy()
    target[0] = np.radians(joint1_deg)
    print(
        f"\n[{zone} 구역] 시작 자세 joint1={joint1_deg:+.0f}도로 "
        f"{MOVE_DURATION_SEC:.0f}초 동안 이동합니다."
    )
    arm.move_joints(target, duration=MOVE_DURATION_SEC)
    time.sleep(SETTLE_TIME_SEC)


def teach_one_pose(arm, cap, zone, expected_joint1_deg):
    window = f"Teach zone {zone} camera pose"
    print(f"[{zone} 구역] 로봇팔을 반드시 손으로 받치세요.")
    print("토크가 풀리면 카메라가 해당 구역 전체를 보도록 천천히 조절하세요.")
    print("영상 창에서 S: 저장, Q: 전체 취소")

    saved_joints = None
    with arm.teach():
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

            current = np.asarray(arm.joints(), dtype=float).copy()
            current_deg = np.degrees(current)
            cv2.putText(
                frame,
                f"Zone {zone} | joint1 {current_deg[0]:+.1f} deg",
                (15, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "Support arm | S: save | Q: cancel",
                (15, frame.shape[0] - 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (0, 0, 255),
                2,
            )
            cv2.imshow(window, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("s"), ord("S")):
                if abs(current_deg[0] - expected_joint1_deg) > 35.0:
                    print(
                        f"[저장 안 함] {zone} 구역 joint1={current_deg[0]:.1f}도입니다. "
                        f"{expected_joint1_deg:+.0f}도 부근으로 맞춘 뒤 S를 다시 누르세요."
                    )
                    continue
                saved_joints = current
                break
            if key in (ord("q"), ord("Q")):
                break

    cv2.destroyWindow(window)
    if saved_joints is None:
        raise KeyboardInterrupt

    print(
        f"[{zone} 저장] 관절각 [deg]: "
        f"{np.round(np.degrees(saved_joints), 1).tolist()}"
    )
    return saved_joints


def main():
    arm = None
    cap = None
    saved = {}

    try:
        settings = load_camera_settings()
        cap = open_camera(settings)

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        # Teach only the physical right-side view at -90 degrees.
        move_to_initial_view(
            arm,
            settings["base_joints"],
            B_INITIAL_JOINT1_DEG,
            "B",
        )
        saved["B"] = teach_one_pose(
            arm,
            cap,
            "B",
            B_INITIAL_JOINT1_DEG,
        )

        # Mirror only joint1 for zone A. Camera tilt joints 2-5 are copied.
        saved["A"] = saved["B"].copy()
        saved["A"][0] = -saved["B"][0]
        print(
            "[A 자동 생성] B 자세에서 joint1 부호만 반대로 바꿨습니다."
        )
        print(
            "[A 관절각 deg]: "
            f"{np.round(np.degrees(saved['A']), 1).tolist()}"
        )

        output = {
            "camera": {
                "index": settings["index"],
                "width": settings["width"],
                "height": settings["height"],
            },
            "zones": {
                zone: {
                    "joints_rad": saved[zone].tolist(),
                    "joints_deg": np.degrees(saved[zone]).tolist(),
                }
                for zone in ("A", "B")
            },
        }
        OUTPUT_PATH.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nA/B 촬영 자세를 저장했습니다: {OUTPUT_PATH}")

    except KeyboardInterrupt:
        print("\n사용자가 자세 저장을 취소했습니다. 기존 JSON은 변경하지 않았습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
