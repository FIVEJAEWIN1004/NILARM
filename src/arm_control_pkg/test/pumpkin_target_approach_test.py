"""Detect one pumpkin and move only to a safe point above it.

This program never descends to the pumpkin and never operates the gripper.
Video controls: M selects a stable target, Q cancels and parks.
After M, the terminal requires the exact word MOVE before any target motion.
"""

import json
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower


MODEL_PATH = Path(
    "/home/chaeyoung/KSAM/NILARM/src/vision_pkg/models/nil_pumpkin.pt"
)
CALIBRATION_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")

CONFIDENCE = 0.25
YOLO_IMAGE_SIZE = 416
TARGET_CLASS_NAMES = {"nil_pumpkin", "pumpkin"}

CAMERA_MOVE_SEC = 6.0
TARGET_MOVE_SEC = 5.0
SAFE_CLEARANCE_M = 0.08
STABLE_SAMPLES = 8
MAX_SPREAD_M = 0.012


def checked_array(value, shape, name):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} 값이 올바르지 않습니다: {array.shape}")
    return array


def load_calibration():
    if not CALIBRATION_PATH.is_file():
        raise FileNotFoundError(
            f"보정 파일이 없습니다: {CALIBRATION_PATH}\n"
            "먼저 pumpkin_plane_calibration.py를 실행하세요."
        )

    data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    camera = data["camera"]
    pose = data["camera_pose"]
    grasp = data["grasp"]

    result = {
        "camera_index": int(camera["index"]),
        "width": int(camera["width"]),
        "height": int(camera["height"]),
        "camera_joints": checked_array(
            pose["joints_rad"], (5,), "camera_pose.joints_rad"
        ),
        "image_points": checked_array(
            data["image_points_px"], (4, 2), "image_points_px"
        ),
        "robot_points": checked_array(
            data["robot_points_xy_m"], (4, 2), "robot_points_xy_m"
        ),
        "homography": checked_array(
            data["homography_px_to_robot_xy"], (3, 3), "homography"
        ),
        "grasp_z": float(grasp["grasp_z_m"]),
        "tool_pitch": float(grasp["tool_pitch_rad"]),
    }

    if not np.isfinite(result["grasp_z"]):
        raise ValueError("grasp_z_m 값이 올바르지 않습니다.")
    if not np.isfinite(result["tool_pitch"]):
        raise ValueError("tool_pitch_rad 값이 올바르지 않습니다.")
    return result


def open_camera(calibration):
    cap = cv2.VideoCapture(calibration["camera_index"], cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, calibration["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, calibration["height"])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(
            f"카메라 /dev/video{calibration['camera_index']}를 열 수 없습니다."
        )

    for _ in range(6):
        cap.read()
    return cap


def normalize_name(value):
    return str(value).strip().lower()


def validate_model(model):
    names = model.names.values() if isinstance(model.names, dict) else model.names
    available = {normalize_name(name) for name in names}
    if not available.intersection(TARGET_CLASS_NAMES):
        raise ValueError(
            "모델 클래스에 nil_pumpkin 또는 pumpkin이 없습니다. "
            f"model.names={model.names}"
        )


def inside_polygon(point, polygon):
    hull = cv2.convexHull(np.asarray(polygon, dtype=np.float32))
    return cv2.pointPolygonTest(hull, point, False) >= 0


def pixel_to_robot(u, v, homography):
    pixel = np.asarray([[[u, v]]], dtype=np.float32)
    xy = cv2.perspectiveTransform(pixel, homography)[0, 0]
    return float(xy[0]), float(xy[1])


def detect_best(model, frame, calibration):
    result = model.predict(
        source=frame,
        conf=CONFIDENCE,
        imgsz=YOLO_IMAGE_SIZE,
        device="cpu",
        verbose=False,
    )[0]
    valid = []

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = normalize_name(model.names[class_id])
        if class_name not in TARGET_CLASS_NAMES:
            continue

        confidence = float(box.conf[0].item())
        x1, y1, x2, y2 = [float(x) for x in box.xyxy[0].tolist()]
        u = (x1 + x2) / 2.0
        v = (y1 + y2) / 2.0

        if not inside_polygon((u, v), calibration["image_points"]):
            continue

        robot_x, robot_y = pixel_to_robot(u, v, calibration["homography"])
        if not inside_polygon(
            (robot_x, robot_y), calibration["robot_points"]
        ):
            continue

        valid.append(
            {
                "confidence": confidence,
                "u": u,
                "v": v,
                "x": robot_x,
                "y": robot_y,
            }
        )

    best = max(valid, key=lambda item: item["confidence"], default=None)
    return result, best


def get_stable_xy(history):
    if len(history) < STABLE_SAMPLES:
        return None

    points = np.asarray([[p["x"], p["y"]] for p in history], dtype=float)
    median = np.median(points, axis=0)
    spread = np.max(np.linalg.norm(points - median, axis=1))
    if spread > MAX_SPREAD_M:
        return None
    return float(median[0]), float(median[1])


def choose_target(model, cap, calibration):
    window = "Pumpkin approach test - M move / Q cancel"
    history = deque(maxlen=STABLE_SAMPLES)
    boundary = cv2.convexHull(
        np.asarray(calibration["image_points"], dtype=np.int32)
    )

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    print("영상의 청록색 보정 영역 안에 호박 하나만 놓으세요.")
    print("STABLE이 표시되면 M, 취소하려면 Q를 누르세요.")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

        result, candidate = detect_best(model, frame, calibration)
        annotated = result.plot()
        cv2.polylines(annotated, [boundary], True, (255, 255, 0), 2)

        if candidate is None:
            history.clear()
            status = "No valid pumpkin inside calibrated area"
            color = (0, 0, 255)
        else:
            history.append(candidate)
            cv2.circle(
                annotated,
                (int(candidate["u"]), int(candidate["v"])),
                7,
                (0, 255, 255),
                -1,
            )
            cv2.putText(
                annotated,
                f"XY=({candidate['x']:.3f}, {candidate['y']:.3f}) m",
                (15, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
            )
            if get_stable_xy(history) is None:
                status = f"Stabilizing {len(history)}/{STABLE_SAMPLES}"
                color = (0, 165, 255)
            else:
                status = "STABLE - Press M"
                color = (0, 255, 0)

        cv2.putText(
            annotated,
            status,
            (15, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
        cv2.putText(
            annotated,
            "Cyan line = calibrated area",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 0),
            2,
        )
        cv2.imshow(window, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            return None
        if key in (ord("m"), ord("M")):
            selected = get_stable_xy(history)
            if selected is not None:
                return selected
            print("아직 좌표가 안정되지 않았습니다.")

        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            return None


def main():
    arm = None
    cap = None

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        calibration = load_calibration()
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        print("YOLO 클래스:", model.names)

        cap = open_camera(calibration)
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("보정할 때 사용한 카메라 자세로 이동합니다.")
        arm.move_joints(
            calibration["camera_joints"], duration=CAMERA_MOVE_SEC
        )
        time.sleep(0.8)

        selected = choose_target(model, cap, calibration)
        cap.release()
        cap = None
        cv2.destroyAllWindows()

        if selected is None:
            print("목표 선택을 취소했습니다.")
            return

        target_x, target_y = selected
        test_z = calibration["grasp_z"] + SAFE_CLEARANCE_M

        print("\n선택된 안전 테스트 좌표:")
        print(f"x={target_x:.4f} m")
        print(f"y={target_y:.4f} m")
        print(f"z={test_z:.4f} m (잡기 위치보다 8cm 위)")
        print("그리퍼를 열거나 닫지 않고 위쪽까지만 이동합니다.")

        answer = input("실제로 이동하려면 대문자로 MOVE를 입력하세요: ")
        if answer.strip() != "MOVE":
            print("이동을 취소했습니다.")
            return

        arm.move_to(
            target_x,
            target_y,
            test_z,
            duration=TARGET_MOVE_SEC,
            pitch=calibration["tool_pitch"],
        )

        input("그리퍼 중심이 호박 위에 있는지 확인하고 Enter를 누르세요: ")
        print("카메라 촬영 자세로 돌아갑니다.")
        arm.move_joints(
            calibration["camera_joints"], duration=CAMERA_MOVE_SEC
        )

    except KeyboardInterrupt:
        print("\n사용자가 중단했습니다.")
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
