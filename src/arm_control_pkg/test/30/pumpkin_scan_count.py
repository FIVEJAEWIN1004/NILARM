"""Scan around the saved camera pose and estimate unique pumpkin count.

Joints 2-5 stay at the calibrated camera pose. Only joint1 moves, in roughly
30-degree steps between -140 and +140 degrees relative to that pose. YOLO
detections are projected to the ground plane and rotated into the OMX base
frame. Nearby detections are merged so a pumpkin seen from overlapping views
is counted once.

This program does not approach or pick pumpkins. Press Q in the video window
or Ctrl-C in the terminal to stop. The arm returns to the camera pose and then
parks in the finally block.
"""

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower


MODEL_PATH = Path(
    "/home/chaeyoung/KSAM/NILARM/src/vision_pkg/models/nil_pumpkin.pt"
)
CALIBRATION_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")
GRASP_XY_CALIBRATION_PATH = Path(__file__).with_name(
    "pumpkin_grasp_xy_calibration.json"
)

CONFIDENCE = 0.70
YOLO_IMAGE_SIZE = 416
TARGET_CLASS_NAMES = {"nil_pumpkin", "pumpkin"}

# Start at the physical right side and sweep once toward the left side.
# The last step is 10 degrees so the scan stays inside the +/-140-degree margin.
SCAN_OFFSETS_DEG = [
    -140,
    -110,
    -80,
    -50,
    -20,
    10,
    40,
    70,
    100,
    130,
    140,
]

MOVE_DURATION_SEC = 6.0
FIRST_MOVE_DURATION_SEC = 5.0
SETTLE_TIME_SEC = 0.7
VIEW_TIME_SEC = 2.0

# Detections closer than this are treated as the same pumpkin.
DUPLICATE_DISTANCE_M = 0.05
MIN_HITS = 3

# Standard OMX joint1 positive rotation is treated as positive XY rotation.
# Change to -1.0 only if a physical coordinate check proves it is reversed.
JOINT1_ROTATION_SIGN = 1.0
JOINT1_SAFE_LIMIT_DEG = 145.0


@dataclass
class Cluster:
    x: float
    y: float
    confidence: float
    hits: int = 1
    views: set[int] = field(default_factory=set)

    def add(self, x, y, confidence, view_index):
        new_hits = self.hits + 1
        self.x = (self.x * self.hits + x) / new_hits
        self.y = (self.y * self.hits + y) / new_hits
        self.hits = new_hits
        self.confidence = max(self.confidence, confidence)
        self.views.add(view_index)


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

    grasp_xy_affine = np.asarray(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        dtype=float,
    )
    if GRASP_XY_CALIBRATION_PATH.is_file():
        grasp_xy_data = json.loads(
            GRASP_XY_CALIBRATION_PATH.read_text(encoding="utf-8")
        )
        grasp_xy_affine = checked_array(
            grasp_xy_data["affine_detected_to_actual_xy"],
            (2, 3),
            "affine_detected_to_actual_xy",
        )
        print(f"그리퍼 XY 보정을 적용합니다: {GRASP_XY_CALIBRATION_PATH}")
    else:
        print("그리퍼 XY 보정 파일이 없어 기존 평면 보정만 사용합니다.")

    return {
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
        "grasp_xy_affine": grasp_xy_affine,
    }


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


def movement_duration(delta_deg):
    """Keep large joint1 moves as slow as a normal 30-degree scan step."""
    return max(
        MOVE_DURATION_SEC,
        abs(float(delta_deg)) / 30.0 * MOVE_DURATION_SEC,
    )


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


def pixel_to_reference_xy(u, v, homography):
    pixel = np.asarray([[[u, v]]], dtype=np.float32)
    xy = cv2.perspectiveTransform(pixel, homography)[0, 0]
    return float(xy[0]), float(xy[1])


def correct_reference_xy(x, y, affine):
    corrected = affine @ np.asarray([x, y, 1.0], dtype=float)
    return float(corrected[0]), float(corrected[1])


def rotate_to_scan_frame(x, y, offset_deg):
    angle = math.radians(offset_deg * JOINT1_ROTATION_SIGN)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return cosine * x - sine * y, sine * x + cosine * y


def add_to_clusters(clusters, x, y, confidence, view_index):
    nearest = None
    nearest_distance = float("inf")

    for cluster in clusters:
        distance = math.hypot(cluster.x - x, cluster.y - y)
        if distance < nearest_distance:
            nearest = cluster
            nearest_distance = distance

    if nearest is not None and nearest_distance <= DUPLICATE_DISTANCE_M:
        nearest.add(x, y, confidence, view_index)
    else:
        clusters.append(
            Cluster(
                x=x,
                y=y,
                confidence=confidence,
                views={view_index},
            )
        )


def valid_clusters(clusters):
    return [cluster for cluster in clusters if cluster.hits >= MIN_HITS]


def detect_frame(model, frame, calibration, offset_deg):
    result = model.predict(
        source=frame,
        conf=CONFIDENCE,
        imgsz=YOLO_IMAGE_SIZE,
        device="cpu",
        verbose=False,
    )[0]
    detections = []

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

        raw_reference_x, raw_reference_y = pixel_to_reference_xy(
            u, v, calibration["homography"]
        )
        if not inside_polygon(
            (raw_reference_x, raw_reference_y), calibration["robot_points"]
        ):
            continue

        reference_x, reference_y = correct_reference_xy(
            raw_reference_x,
            raw_reference_y,
            calibration["grasp_xy_affine"],
        )

        world_x, world_y = rotate_to_scan_frame(
            reference_x, reference_y, offset_deg
        )
        detections.append(
            {
                "u": u,
                "v": v,
                "x": world_x,
                "y": world_y,
                "confidence": confidence,
            }
        )

    return result, detections


def observe_view(
    model,
    cap,
    calibration,
    offset_deg,
    view_index,
    global_clusters,
    display_state,
):
    window = "Pumpkin 360 scan - Q stop"
    view_clusters = []
    deadline = time.monotonic() + VIEW_TIME_SEC

    for _ in range(3):
        cap.read()

    while time.monotonic() < deadline:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

        result, detections = detect_frame(
            model, frame, calibration, offset_deg
        )
        for detection in detections:
            add_to_clusters(
                view_clusters,
                detection["x"],
                detection["y"],
                detection["confidence"],
                view_index,
            )
            add_to_clusters(
                global_clusters,
                detection["x"],
                detection["y"],
                detection["confidence"],
                view_index,
            )

        # Draw only YOLO detection boxes. The large mint calibration-area
        # outline stays hidden, while the boundary is still used internally.
        annotated = result.plot()
        cv2.putText(
            annotated,
            f"Joint1 offset: {offset_deg:+.0f} deg",
            (15, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            annotated,
            f"Current unique: {len(valid_clusters(view_clusters))}",
            (15, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
        )
        if display_state["show_total"]:
            cv2.putText(
                annotated,
                f"Overall unique: {len(valid_clusters(global_clusters))}",
                (15, 98),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )
        cv2.putText(
            annotated,
            "ENTER: overall count | Q: stop and park",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
        cv2.imshow(window, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            return len(valid_clusters(view_clusters)), True
        if key in (10, 13):
            display_state["show_total"] = True
            total_count = len(valid_clusters(global_clusters))
            print(f"[전체 개수] 현재까지 중복 제거된 호박: {total_count}개")
        try:
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                return len(valid_clusters(view_clusters)), True
        except cv2.error:
            return len(valid_clusters(view_clusters)), True

    return len(valid_clusters(view_clusters)), False


def print_summary(view_results, clusters):
    unique = valid_clusters(clusters)
    print("\n========== 호박 스캔 결과 ==========")
    for offset_deg, count in view_results:
        print(f"joint1 기준 {offset_deg:+.0f}도: 화면 내 {count}개")

    print(f"\n중복 제거 후 예상 전체 호박 수: {len(unique)}개")
    for index, cluster in enumerate(unique, start=1):
        degrees = [SCAN_OFFSETS_DEG[i] for i in sorted(cluster.views)]
        print(
            f"{index:02d}. xy=({cluster.x:.3f}, {cluster.y:.3f}) m, "
            f"confidence={cluster.confidence:.2f}, views={degrees}"
        )
    print("====================================")
    print("개수는 YOLO 오검출과 좌표 보정 오차에 따라 달라질 수 있습니다.")


def main():
    arm = None
    cap = None
    calibration = None

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

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        print("저장된 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)
        print(f"기준 joint1 절대각도: {base_joint1_deg:.1f}도")

        global_clusters = []
        view_results = []
        display_state = {"show_total": False}
        current_offset_deg = 0.0

        for view_index, offset_deg in enumerate(SCAN_OFFSETS_DEG):
            target_joint1_deg = base_joint1_deg + offset_deg
            if abs(target_joint1_deg) > JOINT1_SAFE_LIMIT_DEG:
                print(
                    f"[건너뜀] offset={offset_deg:+.0f}도, "
                    f"joint1={target_joint1_deg:.1f}도: 안전 범위 밖"
                )
                continue

            target_joints = camera_joints.copy()
            target_joints[0] = np.radians(target_joint1_deg)
            print(
                f"[이동] 기준 {offset_deg:+.0f}도 "
                f"(joint1={target_joint1_deg:.1f}도)"
            )
            delta_deg = offset_deg - current_offset_deg
            if view_index == 0:
                move_duration = FIRST_MOVE_DURATION_SEC
            else:
                move_duration = movement_duration(delta_deg)
            print(f"[속도] 이번 이동 시간: {move_duration:.1f}초")
            arm.move_joints(target_joints, duration=move_duration)
            current_offset_deg = offset_deg
            time.sleep(SETTLE_TIME_SEC)

            count, stop = observe_view(
                model,
                cap,
                calibration,
                offset_deg,
                view_index,
                global_clusters,
                display_state,
            )
            view_results.append((offset_deg, count))
            print(f"[인식] 기준 {offset_deg:+.0f}도: 화면 내 {count}개")
            if stop:
                break

        print_summary(view_results, global_clusters)

    except KeyboardInterrupt:
        print("\n사용자가 스캔을 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if calibration is not None:
                    print("저장된 카메라 자세로 돌아갑니다.")
                    arm.move_joints(
                        calibration["camera_joints"],
                        duration=movement_duration(140.0),
                    )
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
