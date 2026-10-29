#!/usr/bin/env python3
"""Preview arm-camera YOLO and HSV results without controlling robot hardware.

This module deliberately contains no OMX, gripper, or ROS action imports.  It
opens only the verified Innomaker camera and never converts pixels into robot
coordinates or commands motion.
"""

from __future__ import annotations

import cv2
from ultralytics import YOLO

from .. import pumpkin_detected_approach_validation as base
from .. import pumpkin_orange_hsv_filter as hsv_filter


WINDOW_NAME = "NILARM camera-only YOLO/HSV check - Q or ESC to quit"


def main() -> None:
    cap = None
    try:
        calibration = base.load_calibrations()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("카메라 전용 모드: OMX 로봇팔과 그리퍼를 연결하거나 움직이지 않습니다.")
        print("Q 또는 ESC: 종료")
        print(
            "주의: 팔이 저장된 보정 카메라 자세와 다르면 하늘색 보정 경계는 "
            "실제 로봇 좌표 영역과 일치하지 않습니다."
        )

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("팔 카메라 프레임을 읽지 못했습니다.")
            if frame.shape[:2] != (base.CAMERA_HEIGHT, base.CAMERA_WIDTH):
                raise RuntimeError(
                    f"영상 크기가 {frame.shape[1]}x{frame.shape[0]}입니다. "
                    f"필요한 크기는 {base.CAMERA_WIDTH}x{base.CAMERA_HEIGHT}입니다."
                )

            display, _counts = hsv_filter.annotate_detections(
                model, frame, calibration
            )
            cv2.imshow(WINDOW_NAME, display)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
