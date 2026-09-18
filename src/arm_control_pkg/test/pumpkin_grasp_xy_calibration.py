"""Calibrate detected pumpkin XY positions against actual gripper XY poses."""

import json
import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from pumpkin_scan_count import (
    CONFIDENCE,
    GRASP_XY_CALIBRATION_PATH,
    MODEL_PATH,
    MOVE_DURATION_SEC,
    SETTLE_TIME_SEC,
    TARGET_CLASS_NAMES,
    YOLO_IMAGE_SIZE,
    load_calibration,
    inside_polygon,
    normalize_name,
    open_camera,
    pixel_to_reference_xy,
    validate_model,
)


POINT_COUNT = 6
WINDOW_NAME = "Pumpkin grasp XY calibration - S capture / Q stop"


def best_raw_detection(model, frame, calibration):
    result = model.predict(
        source=frame,
        conf=CONFIDENCE,
        imgsz=YOLO_IMAGE_SIZE,
        device="cpu",
        verbose=False,
    )[0]
    candidates = []

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = normalize_name(model.names[class_id])
        if class_name not in TARGET_CLASS_NAMES:
            continue

        confidence = float(box.conf[0].item())
        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        u = (x1 + x2) / 2.0
        v = (y1 + y2) / 2.0
        if not inside_polygon((u, v), calibration["image_points"]):
            continue
        x, y = pixel_to_reference_xy(u, v, calibration["homography"])
        if not inside_polygon((x, y), calibration["robot_points"]):
            continue
        candidates.append(
            {
                "u": u,
                "v": v,
                "x": x,
                "y": y,
                "confidence": confidence,
            }
        )

    best = max(candidates, key=lambda item: item["confidence"], default=None)
    return result, best


def capture_one_point(model, cap, calibration, point_number):
    for _ in range(5):
        cap.read()

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

        result, best = best_raw_detection(model, frame, calibration)
        annotated = result.plot()
        cv2.putText(
            annotated,
            f"Point {point_number}/{POINT_COUNT}",
            (15, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
        )

        if best is None:
            message = "Show exactly one pumpkin"
            color = (0, 0, 255)
        else:
            message = (
                f"S: capture  XY=({best['x']:.3f}, {best['y']:.3f})"
            )
            color = (0, 255, 255)

        cv2.putText(
            annotated,
            message,
            (15, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            color,
            2,
        )
        cv2.putText(
            annotated,
            "Q: cancel",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
        cv2.imshow(WINDOW_NAME, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            raise KeyboardInterrupt
        if key in (ord("s"), ord("S")) and best is not None:
            return best


def fit_affine(detected_points, actual_points):
    detected = np.asarray(detected_points, dtype=float)
    actual = np.asarray(actual_points, dtype=float)
    design = np.column_stack([detected, np.ones(len(detected))])

    coefficients, _, rank, _ = np.linalg.lstsq(design, actual, rcond=None)
    if rank < 3:
        raise ValueError(
            "측정점이 한쪽에 몰려 보정행렬을 계산할 수 없습니다. "
            "호박을 화면 전체에 고르게 배치해 다시 실행하세요."
        )

    affine = coefficients.T
    estimated = design @ coefficients
    errors = np.linalg.norm(estimated - actual, axis=1)
    return affine, estimated, errors


def main():
    arm = None
    cap = None

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        calibration = load_calibration()
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        cap = open_camera(calibration)

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)
        camera_joints = calibration["camera_joints"]
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)

        detected_points = []
        actual_points = []
        records = []

        print("\n호박 1개만 사용해 서로 다른 6개 위치를 측정합니다.")
        print("가까운 곳/먼 곳/왼쪽/오른쪽/중간에 고르게 배치하세요.")

        for index in range(POINT_COUNT):
            input(
                f"\n[{index + 1}/{POINT_COUNT}] 호박을 새 위치에 놓고 "
                "손을 치운 뒤 Enter: "
            )
            detection = capture_one_point(
                model,
                cap,
                calibration,
                index + 1,
            )
            cv2.destroyWindow(WINDOW_NAME)
            detected_xy = [detection["x"], detection["y"]]
            print(
                f"YOLO 변환 좌표: "
                f"({detected_xy[0]:.4f}, {detected_xy[1]:.4f}) m"
            )

            print("teach 모드로 전환합니다. 팔을 반드시 양손으로 받치세요.")
            with arm.teach():
                input(
                    "그리퍼 중심을 호박의 실제 잡기 중심에 맞춘 뒤 Enter: "
                )
                actual_pose = arm.pose().copy()

            actual_xy = [float(actual_pose[0]), float(actual_pose[1])]
            detected_points.append(detected_xy)
            actual_points.append(actual_xy)
            records.append(
                {
                    "pixel_uv": [detection["u"], detection["v"]],
                    "confidence": detection["confidence"],
                    "detected_xy_m": detected_xy,
                    "actual_xy_m": actual_xy,
                }
            )
            print(
                f"실제 그리퍼 좌표: "
                f"({actual_xy[0]:.4f}, {actual_xy[1]:.4f}) m"
            )
            print(
                f"차이: dx={(actual_xy[0] - detected_xy[0]) * 1000:.1f} mm, "
                f"dy={(actual_xy[1] - detected_xy[1]) * 1000:.1f} mm"
            )

            input("팔과 호박 주변을 정리한 뒤 Enter를 누르면 카메라 자세로 복귀: ")
            arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

        affine, estimated, errors = fit_affine(
            detected_points,
            actual_points,
        )
        mean_error_mm = float(np.mean(errors) * 1000.0)
        max_error_mm = float(np.max(errors) * 1000.0)

        print("\n========== XY 보정 결과 ==========")
        print("보정행렬:\n", np.round(affine, 6))
        print(f"평균 잔차: {mean_error_mm:.1f} mm")
        print(f"최대 잔차: {max_error_mm:.1f} mm")
        print("==================================")

        answer = input("이 보정값을 저장하려면 SAVE 입력: ").strip()
        if answer != "SAVE":
            print("저장하지 않았습니다.")
            return

        output = {
            "point_count": POINT_COUNT,
            "affine_detected_to_actual_xy": affine.tolist(),
            "mean_error_mm": mean_error_mm,
            "max_error_mm": max_error_mm,
            "records": records,
        }
        GRASP_XY_CALIBRATION_PATH.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"보정값을 저장했습니다: {GRASP_XY_CALIBRATION_PATH}")

    except KeyboardInterrupt:
        print("\n사용자가 XY 보정을 중단했습니다.")
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
