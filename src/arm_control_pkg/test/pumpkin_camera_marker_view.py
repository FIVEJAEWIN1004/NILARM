#!/usr/bin/env python3
"""Move to the saved camera pose and show the Innomaker camera live view.

Use this live view to place nine calibration markers on the table.  This file
does not teach points, calculate calibration, or save calibration data.

Controls:
    G       show/hide the 3 x 3 placement guide
    S       save the current frame beside this script
    Q / ESC close the viewer
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


CAMERA_DEVICE_PATH = Path(
    "/dev/v4l/by-id/usb-Innomaker_Innomaker-U20CAM-720P_SN0001-video-index0"
)
CAMERA_INDEX_FALLBACK = 2
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
WINDOW_NAME = "Pumpkin marker live view - G guide / S save / Q quit"
CAMERA_POSE_PATH = Path(__file__).with_name("camera_view_pose.json")
CAMERA_MOVE_DURATION_SEC = 6.0
SETTLE_TIME_SEC = 1.0


def load_camera_joints() -> np.ndarray:
    if not CAMERA_POSE_PATH.is_file():
        raise FileNotFoundError(
            f"카메라 자세 파일이 없습니다: {CAMERA_POSE_PATH}"
        )

    data = json.loads(CAMERA_POSE_PATH.read_text(encoding="utf-8"))
    joints = np.asarray(data.get("joints_rad"), dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError("camera_view_pose.json의 joints_rad가 올바르지 않습니다.")
    return joints


def open_camera() -> tuple[cv2.VideoCapture, str]:
    if CAMERA_DEVICE_PATH.exists():
        source: str | int = str(CAMERA_DEVICE_PATH)
        source_name = str(CAMERA_DEVICE_PATH)
    else:
        source = CAMERA_INDEX_FALLBACK
        source_name = f"/dev/video{CAMERA_INDEX_FALLBACK} (fallback)"

    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        cap.release()
        raise RuntimeError(
            "팔 카메라를 열 수 없습니다. 다른 카메라 프로그램을 닫고 "
            f"{source_name} 연결을 확인하세요."
        )

    for _ in range(10):
        ok, _ = cap.read()
        if not ok:
            cap.release()
            raise RuntimeError(f"{source_name}에서 영상을 읽지 못했습니다.")

    return cap, source_name


def draw_guide(frame):
    """Draw a visual guide only; these circles are not calibration samples."""
    height, width = frame.shape[:2]
    xs = (int(width * 0.20), int(width * 0.50), int(width * 0.80))
    ys = (int(height * 0.20), int(height * 0.50), int(height * 0.80))

    number = 1
    for y in ys:
        for x in xs:
            cv2.circle(frame, (x, y), 10, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.drawMarker(
                frame,
                (x, y),
                (0, 255, 255),
                cv2.MARKER_CROSS,
                20,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                str(number),
                (x + 13, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )
            number += 1

    cv2.putText(
        frame,
        "GUIDE ONLY - use reachable points on the table",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main() -> None:
    print("저장된 보정 촬영 자세로 이동한 뒤 카메라만 실시간 표시합니다.")
    print("점 교육, 좌표 계산, 보정 파일 저장은 하지 않습니다.")
    print("G: 3x3 안내점 표시/숨김, S: 화면 저장, Q 또는 ESC: 종료")

    arm = None
    cap = None

    show_guide = False
    try:
        camera_joints = load_camera_joints()
        print("촬영 관절각 [deg]:", np.round(np.degrees(camera_joints), 1))

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)
        print("저장된 카메라 촬영 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=CAMERA_MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)

        cap, source_name = open_camera()
        print(f"카메라 열림: {source_name}")

        while True:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("카메라 프레임을 읽는 중 연결이 끊겼습니다.")

            display = frame.copy()
            if show_guide:
                draw_guide(display)

            cv2.putText(
                display,
                "G:guide  S:save  Q/ESC:quit",
                (12, display.shape[0] - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            if key in (ord("g"), ord("G")):
                show_guide = not show_guide
            if key in (ord("s"), ord("S")):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(__file__).with_name(
                    f"pumpkin_marker_view_{timestamp}.png"
                )
                if cv2.imwrite(str(output_path), frame):
                    print(f"원본 화면 저장: {output_path}")
                else:
                    print(f"화면 저장 실패: {output_path}")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("카메라를 닫았습니다.")
        if arm is not None:
            try:
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
