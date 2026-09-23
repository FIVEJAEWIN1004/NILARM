#!/usr/bin/env python3
"""Preview YOLO pumpkin detections with HSV orange/green classification.

The arm moves only to one selected folded scan pose. Every detected pumpkin is
labelled ORANGE, GREEN, or UNKNOWN from the inner body region of its YOLO box.
This program never approaches a pumpkin and never operates the gripper.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
import pumpkin_detected_approach_validation as base
import pumpkin_multiangle_approach_validation as multi


WINDOW_NAME = "Pumpkin HSV check - ORANGE harvest / Q quit / S save"

# OpenCV HSV ranges: H=0..179, S=0..255, V=0..255.
# These are deliberately separated so ambiguous pixels become UNKNOWN.
ORANGE_HSV_LOW = np.asarray([0, 80, 45], dtype=np.uint8)
ORANGE_HSV_HIGH = np.asarray([28, 255, 255], dtype=np.uint8)
# Red-orange can wrap to the top end of OpenCV's 0..179 hue scale.
ORANGE_WRAP_HSV_LOW = np.asarray([170, 80, 45], dtype=np.uint8)
ORANGE_WRAP_HSV_HIGH = np.asarray([179, 255, 255], dtype=np.uint8)
GREEN_HSV_LOW = np.asarray([32, 55, 35], dtype=np.uint8)
GREEN_HSV_HIGH = np.asarray([95, 255, 255], dtype=np.uint8)

# Remove box edges/background and the upper stem area before colour analysis.
BODY_SIDE_CROP_FRACTION = 0.14
BODY_TOP_CROP_FRACTION = 0.22
BODY_BOTTOM_CROP_FRACTION = 0.06
MIN_CLASS_RATIO = 0.22
WINNER_MARGIN = 1.25
MIN_BODY_SIZE_PX = 12


def clamp_box(box, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = (float(value) for value in box)
    return (
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(0, min(width, int(round(x2)))),
        max(0, min(height, int(round(y2)))),
    )


def body_region(box, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = clamp_box(box, width, height)
    box_width = max(0, x2 - x1)
    box_height = max(0, y2 - y1)
    left = x1 + int(round(box_width * BODY_SIDE_CROP_FRACTION))
    right = x2 - int(round(box_width * BODY_SIDE_CROP_FRACTION))
    top = y1 + int(round(box_height * BODY_TOP_CROP_FRACTION))
    bottom = y2 - int(round(box_height * BODY_BOTTOM_CROP_FRACTION))
    return left, top, right, bottom


def classify_pumpkin_hsv(frame: np.ndarray, box) -> dict:
    """Classify one YOLO box from its cropped elliptical body region."""
    height, width = frame.shape[:2]
    left, top, right, bottom = body_region(box, width, height)
    roi_width = right - left
    roi_height = bottom - top
    if roi_width < MIN_BODY_SIZE_PX or roi_height < MIN_BODY_SIZE_PX:
        return {
            "label": "UNKNOWN",
            "orange_ratio": 0.0,
            "green_ratio": 0.0,
            "median_hue": None,
            "body_box": (left, top, right, bottom),
        }

    roi = frame[top:bottom, left:right]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    ellipse = np.zeros((roi_height, roi_width), dtype=np.uint8)
    center = (roi_width // 2, roi_height // 2)
    axes = (
        max(1, int(round(roi_width * 0.48))),
        max(1, int(round(roi_height * 0.48))),
    )
    cv2.ellipse(ellipse, center, axes, 0, 0, 360, 255, -1)

    orange_mask_low = cv2.inRange(hsv, ORANGE_HSV_LOW, ORANGE_HSV_HIGH)
    orange_mask_wrap = cv2.inRange(
        hsv, ORANGE_WRAP_HSV_LOW, ORANGE_WRAP_HSV_HIGH
    )
    orange_mask = cv2.bitwise_or(orange_mask_low, orange_mask_wrap)
    green_mask = cv2.inRange(hsv, GREEN_HSV_LOW, GREEN_HSV_HIGH)
    orange_mask = cv2.bitwise_and(orange_mask, ellipse)
    green_mask = cv2.bitwise_and(green_mask, ellipse)

    body_pixels = max(1, int(cv2.countNonZero(ellipse)))
    orange_ratio = float(cv2.countNonZero(orange_mask)) / body_pixels
    green_ratio = float(cv2.countNonZero(green_mask)) / body_pixels

    chromatic = (hsv[:, :, 1] >= 55) & (hsv[:, :, 2] >= 35) & (ellipse > 0)
    median_hue = (
        float(np.median(hsv[:, :, 0][chromatic]))
        if np.any(chromatic)
        else None
    )

    if (
        orange_ratio >= MIN_CLASS_RATIO
        and orange_ratio >= green_ratio * WINNER_MARGIN
    ):
        label = "ORANGE"
    elif (
        green_ratio >= MIN_CLASS_RATIO
        and green_ratio >= orange_ratio * WINNER_MARGIN
    ):
        label = "GREEN"
    else:
        label = "UNKNOWN"

    return {
        "label": label,
        "orange_ratio": orange_ratio,
        "green_ratio": green_ratio,
        "median_hue": median_hue,
        "body_box": (left, top, right, bottom),
    }


def label_color(label: str) -> tuple[int, int, int]:
    if label == "ORANGE":
        return 0, 140, 255
    if label == "GREEN":
        return 0, 255, 0
    return 180, 180, 180


def annotate_detections(model: YOLO, frame: np.ndarray, calibration):
    result = model.predict(
        source=frame,
        conf=base.CONFIDENCE,
        imgsz=base.YOLO_IMAGE_SIZE,
        device="cpu",
        verbose=False,
    )[0]
    display = frame.copy()
    boundary = cv2.convexHull(
        calibration["image_points"].astype(np.int32).reshape(-1, 1, 2)
    )
    cv2.polylines(display, [boundary], True, (255, 255, 0), 2)

    counts = {"ORANGE": 0, "GREEN": 0, "UNKNOWN": 0}
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = base.normalize_name(model.names[class_id])
        if class_name not in base.TARGET_CLASS_NAMES:
            continue

        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = clamp_box(
            xyxy, display.shape[1], display.shape[0]
        )
        colour = classify_pumpkin_hsv(frame, xyxy)
        label = colour["label"]
        counts[label] += 1
        draw_color = label_color(label)

        cv2.rectangle(display, (x1, y1), (x2, y2), draw_color, 2)
        left, top, right, bottom = colour["body_box"]
        cv2.rectangle(display, (left, top), (right, bottom), (255, 255, 255), 1)

        hue_text = (
            "--" if colour["median_hue"] is None else f"{colour['median_hue']:.0f}"
        )
        text = (
            f"{label} O:{colour['orange_ratio'] * 100:.0f}% "
            f"G:{colour['green_ratio'] * 100:.0f}% H:{hue_text}"
        )
        text_y = max(22, y1 - 8)
        cv2.putText(
            display,
            text,
            (x1, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            draw_color,
            2,
            cv2.LINE_AA,
        )

    summary = (
        f"HARVEST ORANGE ONLY | O:{counts['ORANGE']} "
        f"G:{counts['GREEN']} U:{counts['UNKNOWN']}"
    )
    cv2.putText(
        display,
        summary,
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 140, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        display,
        "White inner box = HSV body sample / S save / Q quit",
        (12, display.shape[0] - 14),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return display, counts


def main() -> None:
    arm = None
    cap = None
    calibration = None
    at_scan_pose = False
    last_display = None

    try:
        calibration = base.load_calibrations()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 프로그램은 HSV로 초록·주황 호박을 구분합니다.")
        print("ORANGE만 수확 대상이며 로봇 접근·그리퍼 동작은 없습니다.")
        print("흰색 내부 박스가 실제 HSV 분석 영역입니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        print("중앙 보정 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=base.CAMERA_MOVE_DURATION_SEC)
        time.sleep(base.SETTLE_TIME_SEC)

        offset_deg = multi.ask_offset()
        if offset_deg is None:
            return
        target_joint1_deg = base_joint1_deg + offset_deg
        if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
            raise ValueError(
                f"촬영 joint1={target_joint1_deg:.1f}도가 안전 범위를 벗어납니다."
            )

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        print(f"촬영 offset={offset_deg:+.0f}도로 이동합니다.")
        arm.move_joints(
            view_joints, duration=multi.movement_duration(offset_deg)
        )
        at_scan_pose = True
        time.sleep(base.SETTLE_TIME_SEC)

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        print("Q/ESC: 종료, S: 판정 화면 저장")
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("팔 카메라 프레임을 읽지 못했습니다.")
            if frame.shape[:2] != (base.CAMERA_HEIGHT, base.CAMERA_WIDTH):
                raise RuntimeError(
                    f"영상 크기가 {frame.shape[1]}x{frame.shape[0]}입니다."
                )

            display, _counts = annotate_detections(model, frame, calibration)
            last_display = display
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            if key in (ord("s"), ord("S")) and last_display is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(__file__).with_name(
                    f"pumpkin_hsv_check_{timestamp}.png"
                )
                if cv2.imwrite(str(output_path), last_display):
                    print(f"HSV 판정 화면 저장: {output_path}")
                else:
                    print(f"화면 저장 실패: {output_path}")

    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if calibration is not None and at_scan_pose:
                    current = np.asarray(arm.joints(), dtype=float)
                    delta_deg = np.degrees(
                        current[0] - calibration["camera_joints"][0]
                    )
                    print("접힌 상태에서 중앙 카메라 자세로 복귀합니다.")
                    arm.move_joints(
                        calibration["camera_joints"],
                        duration=multi.movement_duration(delta_deg),
                    )
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
