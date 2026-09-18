"""Calibrate pumpkin image pixels directly against the real gripper XY.

This is a calibration-only program. It does not automatically approach or
grasp a pumpkin. It measures four points in zone B (-90-degree view) and then
four points in zone A (+90-degree view), fitting a separate planar homography
from image pixel (u, v) directly to robot-base (x, y) for each zone.

At every point:
1. Put exactly one pumpkin in the requested part of the zone.
2. YOLO captures its stable image position automatically.
3. The arm enters teach mode; support it with both hands.
4. Put the gripper center directly over the pumpkin center and press Enter.

Press Q in the video window or Ctrl-C in the terminal to stop. The arm parks
in the finally block.
"""

import json
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from pumpkin_scan_count import (
    CONFIDENCE,
    MODEL_PATH,
    SETTLE_TIME_SEC,
    TARGET_CLASS_NAMES,
    YOLO_IMAGE_SIZE,
    load_calibration,
    normalize_name,
    open_camera,
    validate_model,
)


POSES_PATH = Path(__file__).with_name("pumpkin_ab_view_poses.json")
OUTPUT_PATH = Path(__file__).with_name(
    "pumpkin_ab_grasp_xy_calibration.json"
)

ZONE_ORDER = ("B", "A")
POINTS_PER_ZONE = 4
MOVE_DURATION_SEC = 10.0
STABLE_FRAME_COUNT = 20
STABLE_PIXEL_RADIUS = 12.0
WINDOW_NAME = "A/B pumpkin grasp XY calibration"

POINT_GUIDES = (
    "카메라 화면의 왼쪽 위쪽",
    "카메라 화면의 오른쪽 위쪽",
    "카메라 화면의 왼쪽 아래쪽",
    "카메라 화면의 오른쪽 아래쪽",
)


def checked_joints(value, name):
    joints = np.asarray(value, dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError(f"{name} 값이 올바르지 않습니다.")
    return joints


def load_zone_poses():
    if not POSES_PATH.is_file():
        raise FileNotFoundError(
            f"A/B 촬영 자세 파일이 없습니다: {POSES_PATH}\n"
            "먼저 pumpkin_ab_pose_teach.py를 실행하세요."
        )

    data = json.loads(POSES_PATH.read_text(encoding="utf-8"))
    return {
        zone: checked_joints(
            data["zones"][zone]["joints_rad"],
            f"zones.{zone}.joints_rad",
        )
        for zone in ZONE_ORDER
    }


def raw_detections(model, frame):
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

        candidates.append(
            {
                "u": u,
                "v": v,
                "confidence": confidence,
            }
        )

    return result, candidates


def capture_one_point(
    model,
    cap,
    calibration,
    zone,
    point_number,
):
    samples = []
    for _ in range(6):
        cap.read()

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

        result, candidates = raw_detections(model, frame)
        annotated = result.plot()

        if len(candidates) != 1:
            samples.clear()
            message = f"Show exactly ONE pumpkin (seen: {len(candidates)})"
            color = (0, 0, 255)
        else:
            detection = candidates[0]
            if samples:
                center_u = float(np.median([item["u"] for item in samples]))
                center_v = float(np.median([item["v"] for item in samples]))
                distance = float(
                    np.hypot(
                        detection["u"] - center_u,
                        detection["v"] - center_v,
                    )
                )
                if distance > STABLE_PIXEL_RADIUS:
                    samples.clear()

            samples.append(detection)
            progress = min(len(samples), STABLE_FRAME_COUNT)
            message = f"Hold still: {progress}/{STABLE_FRAME_COUNT}"
            color = (0, 255, 255)

        cv2.putText(
            annotated,
            f"Zone {zone} | Point {point_number}/{POINTS_PER_ZONE}",
            (15, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            annotated,
            message,
            (15, 66),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            color,
            2,
        )
        cv2.putText(
            annotated,
            "Automatic capture | Q: cancel and park",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2,
        )
        cv2.imshow(WINDOW_NAME, annotated)

        if len(samples) >= STABLE_FRAME_COUNT:
            return {
                "u": float(np.median([item["u"] for item in samples])),
                "v": float(np.median([item["v"] for item in samples])),
                "confidence": float(
                    np.median([item["confidence"] for item in samples])
                ),
            }

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            raise KeyboardInterrupt


def fit_homography(pixel_points, actual_points):
    pixels = np.asarray(pixel_points, dtype=np.float64)
    actual = np.asarray(actual_points, dtype=float)
    homography, _ = cv2.findHomography(pixels, actual, method=0)
    if homography is None or not np.all(np.isfinite(homography)):
        raise ValueError(
            "측정점 배치로 평면 변환을 계산할 수 없습니다. "
            "네 지점을 화면 전체에 고르게 배치해 다시 실행하세요."
        )
    if abs(float(np.linalg.det(homography))) < 1e-12:
        raise ValueError("보정행렬이 불안정합니다. 네 지점을 다시 측정하세요.")

    estimated = cv2.perspectiveTransform(
        pixels.reshape(-1, 1, 2),
        homography,
    ).reshape(-1, 2)
    errors = np.linalg.norm(estimated - actual, axis=1)
    return homography, errors


def main():
    arm = None
    cap = None
    calibration = None

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        zone_poses = load_zone_poses()
        calibration = load_calibration()
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        cap = open_camera(calibration)

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        zone_results = {}

        print("\n이 코드는 XY 보정만 수행하며 호박을 자동으로 잡지 않습니다.")
        print("각 구역에서 호박 1개를 서로 다른 네 위치에 놓으세요.")

        for zone in ZONE_ORDER:
            zone_joints = zone_poses[zone]
            zone_joint1_deg = float(np.degrees(zone_joints[0]))

            print(
                f"\n========== {zone} 구역 "
                f"(joint1={zone_joint1_deg:+.1f}도) =========="
            )
            print("저장된 촬영 자세로 이동합니다.")
            arm.move_joints(zone_joints, duration=MOVE_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            pixel_points = []
            actual_points = []
            records = []

            for point_index, guide in enumerate(POINT_GUIDES, start=1):
                input(
                    f"\n[{zone} {point_index}/{POINTS_PER_ZONE}] "
                    f"호박 1개를 {guide}에 놓고 손을 치운 뒤 Enter: "
                )
                detection = capture_one_point(
                    model,
                    cap,
                    calibration,
                    zone,
                    point_index,
                )
                cv2.destroyWindow(WINDOW_NAME)
                pixel_uv = [detection["u"], detection["v"]]
                print(
                    "YOLO 중심 픽셀: "
                    f"({pixel_uv[0]:.1f}, {pixel_uv[1]:.1f}) px"
                )

                print("teach 모드로 전환합니다. 팔을 반드시 양손으로 받치세요.")
                with arm.teach():
                    input(
                        "그리퍼 중심을 호박 중심 바로 위에 맞춘 뒤 Enter: "
                    )
                    actual_pose = np.asarray(arm.pose(), dtype=float).copy()

                actual_xy = [float(actual_pose[0]), float(actual_pose[1])]
                pixel_points.append(pixel_uv)
                actual_points.append(actual_xy)
                records.append(
                    {
                        "pixel_uv": pixel_uv,
                        "confidence": detection["confidence"],
                        "actual_xy_m": actual_xy,
                    }
                )
                print(
                    "실제 그리퍼 좌표: "
                    f"({actual_xy[0]:.4f}, {actual_xy[1]:.4f}) m"
                )
                input("팔과 주변을 확인한 뒤 Enter를 누르면 촬영 자세로 복귀: ")
                arm.move_joints(zone_joints, duration=MOVE_DURATION_SEC)
                time.sleep(SETTLE_TIME_SEC)

            homography, errors = fit_homography(pixel_points, actual_points)
            mean_error_mm = float(np.mean(errors) * 1000.0)
            max_error_mm = float(np.max(errors) * 1000.0)
            zone_results[zone] = {
                "joint1_deg": zone_joint1_deg,
                "homography_pixel_uv_to_robot_xy": homography.tolist(),
                "mean_error_mm": mean_error_mm,
                "max_error_mm": max_error_mm,
                "records": records,
            }

            print(f"\n[{zone} 픽셀→로봇 XY 보정행렬]\n{np.round(homography, 8)}")
            print(f"네 기준점 재투영 오차: 평균 {mean_error_mm:.3f} mm")

        print("\n========== A/B XY 보정 완료 ==========")
        for zone in ("A", "B"):
            result = zone_results[zone]
            print(
                f"{zone}: 평균 {result['mean_error_mm']:.1f} mm, "
                f"최대 {result['max_error_mm']:.1f} mm"
            )

        answer = input("저장하려면 정확히 SAVE 입력: ").strip()
        if answer != "SAVE":
            print("저장하지 않았습니다.")
            return

        output = {
            "confidence": CONFIDENCE,
            "points_per_zone": POINTS_PER_ZONE,
            "zones": zone_results,
        }
        OUTPUT_PATH.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"A/B 그리퍼 XY 보정값을 저장했습니다: {OUTPUT_PATH}")

    except KeyboardInterrupt:
        print("\n사용자가 보정을 중단했습니다. 새 보정값은 저장하지 않았습니다.")
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
