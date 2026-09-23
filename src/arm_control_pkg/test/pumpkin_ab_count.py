"""Count pumpkins once in taught zone A and zone B camera poses.

The complete five-joint poses are loaded from pumpkin_ab_view_poses.json.
For each zone, YOLO runs for a short period and the most frequently observed
frame count is selected. The final competition-format result is printed as
"A-2 / B-1". Press Q in the video window or Ctrl-C to stop and park.
"""

import json
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower


MODEL_PATH = Path(
    "/home/chaeyoung/KSAM/NILARM/src/vision_pkg/models/nil_pumpkin.pt"
)
POSES_PATH = Path(__file__).with_name("pumpkin_ab_view_poses.json")

CONFIDENCE = 0.70
YOLO_IMAGE_SIZE = 416
TARGET_CLASS_NAMES = {"nil_pumpkin", "pumpkin"}

MOVE_DURATION_SEC = 8.0
SETTLE_TIME_SEC = 0.7
VIEW_TIME_SEC = 5.0
MIN_SAMPLES = 5


def checked_joints(value, name):
    joints = np.asarray(value, dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError(f"{name} 값이 올바르지 않습니다.")
    if np.any(np.abs(np.degrees(joints)) > 175.0):
        raise ValueError(f"{name}에 비정상적으로 큰 관절각이 있습니다.")
    return joints


def load_settings():
    if not POSES_PATH.is_file():
        raise FileNotFoundError(
            f"A/B 촬영 자세 파일이 없습니다: {POSES_PATH}\n"
            "먼저 pumpkin_ab_pose_teach.py를 실행하세요."
        )

    data = json.loads(POSES_PATH.read_text(encoding="utf-8"))
    camera = data["camera"]
    zones = data["zones"]
    return {
        "camera_index": int(camera["index"]),
        "width": int(camera["width"]),
        "height": int(camera["height"]),
        "A": checked_joints(zones["A"]["joints_rad"], "zones.A.joints_rad"),
        "B": checked_joints(zones["B"]["joints_rad"], "zones.B.joints_rad"),
    }


def open_camera(settings):
    cap = cv2.VideoCapture(settings["camera_index"], cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        raise RuntimeError(
            f"카메라 /dev/video{settings['camera_index']}를 열 수 없습니다."
        )
    for _ in range(8):
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


def count_target_boxes(model, result):
    count = 0
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = normalize_name(model.names[class_id])
        confidence = float(box.conf[0].item())
        if class_name in TARGET_CLASS_NAMES and confidence >= CONFIDENCE:
            count += 1
    return count


def stable_count(samples):
    if not samples:
        return 0
    frequencies = Counter(samples)
    # On a frequency tie, choose the smaller count to avoid one-frame
    # duplicate boxes inflating the competition result.
    return max(frequencies, key=lambda count: (frequencies[count], -count))


def observe_zone(model, cap, zone):
    window = "Pumpkin A/B count - Q stop"
    deadline = time.monotonic() + VIEW_TIME_SEC
    samples = []

    for _ in range(5):
        cap.read()

    while time.monotonic() < deadline:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

        result = model.predict(
            source=frame,
            conf=CONFIDENCE,
            imgsz=YOLO_IMAGE_SIZE,
            device="cpu",
            verbose=False,
        )[0]
        frame_count = count_target_boxes(model, result)
        samples.append(frame_count)
        current = stable_count(samples)

        # Keep the YOLO pumpkin boxes. No mint calibration polygon is drawn.
        annotated = result.plot()
        cv2.putText(
            annotated,
            f"Zone {zone}",
            (15, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            annotated,
            f"Stable count: {current}",
            (15, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            annotated,
            "Q: stop and park",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
        cv2.imshow(window, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            return current, True
        try:
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                return current, True
        except cv2.error:
            return current, True

    if len(samples) < MIN_SAMPLES:
        raise RuntimeError("안정적인 개수 계산에 필요한 영상 프레임이 부족합니다.")
    return stable_count(samples), False


def main():
    arm = None
    cap = None
    settings = None
    counts = {}

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        settings = load_settings()
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        print("YOLO 클래스:", model.names)

        cap = open_camera(settings)
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        # Measure the taught -90-degree B view first, then its +90-degree A view.
        for zone in ("B", "A"):
            print(f"\n[{zone} 구역] 저장된 촬영 자세로 이동합니다.")
            print(
                f"관절각 [deg]: "
                f"{np.round(np.degrees(settings[zone]), 1).tolist()}"
            )
            arm.move_joints(settings[zone], duration=MOVE_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            counts[zone], stop = observe_zone(model, cap, zone)
            print(f"[{zone} 구역] 익은 호박 {counts[zone]}개")
            if stop:
                print("사용자가 측정을 중단했습니다.")
                return

        result_text = f"A-{counts['A']} / B-{counts['B']}"
        print("\n========== 구역별 호박 현황 ==========")
        print(result_text)
        print("=======================================")

    except KeyboardInterrupt:
        print("\n사용자가 측정을 중단했습니다.")
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
