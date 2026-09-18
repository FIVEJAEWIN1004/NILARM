"""Move OMX to the saved camera pose and test nil_pumpkin.pt live detection.

The pose is loaded from camera_view_pose.json, produced by camera_pose_teach.py.
Click the video window and press Q to stop. The arm moves to park in the finally
block before disconnecting.
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
CAMERA_POSE_PATH = Path(__file__).with_name("camera_view_pose.json")
CAMERA_INDEX = 0
CONFIDENCE = 0.25
YOLO_IMAGE_SIZE = 416

MOVE_DURATION_SEC = 6.0
SETTLE_TIME_SEC = 0.7


def load_camera_joints():
    """Load and validate the five saved OMX joint angles in radians."""
    if not CAMERA_POSE_PATH.is_file():
        raise FileNotFoundError(
            f"저장된 카메라 자세가 없습니다: {CAMERA_POSE_PATH}\n"
            "먼저 camera_pose_teach.py를 실행해 촬영 자세를 저장하세요."
        )

    data = json.loads(CAMERA_POSE_PATH.read_text(encoding="utf-8"))
    if "joints_rad" not in data:
        raise ValueError("camera_view_pose.json에 joints_rad 항목이 없습니다.")

    joints = np.asarray(data["joints_rad"], dtype=float)
    if joints.shape != (5,):
        raise ValueError(
            "저장된 관절각은 5개여야 합니다. "
            f"현재 형태: {joints.shape}"
        )
    if not np.all(np.isfinite(joints)):
        raise ValueError("저장된 관절각에 올바르지 않은 숫자가 있습니다.")

    return joints


def open_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"카메라 /dev/video{CAMERA_INDEX}를 열 수 없습니다.")

    for _ in range(5):
        cap.read()
    return cap


def draw_detection(model, frame):
    result = model.predict(
        source=frame,
        conf=CONFIDENCE,
        imgsz=YOLO_IMAGE_SIZE,
        device="cpu",
        verbose=False,
    )[0]

    counts = Counter()
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        counts[str(model.names[class_id])] += 1

    # 검출 네모박스, 클래스명, 신뢰도를 그린 영상
    annotated = result.plot()

    cv2.putText(
        annotated,
        "Saved camera pose",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
    )

    y = 70
    for class_name, count in sorted(counts.items()):
        cv2.putText(
            annotated,
            f"{class_name}: {count}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
        y += 30

    cv2.putText(
        annotated,
        "Press Q to park and exit",
        (20, annotated.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2,
    )
    return annotated


def main():
    arm = None
    cap = None

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"모델 파일이 없습니다: {MODEL_PATH}")

        camera_joints = load_camera_joints()
        print("저장된 촬영 관절각 [deg]:", np.round(np.degrees(camera_joints), 1))

        print(f"YOLO 모델을 불러옵니다: {MODEL_PATH}")
        model = YOLO(str(MODEL_PATH))
        print("YOLO 클래스:", model.names)

        cap = open_camera()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("저장된 카메라 촬영 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)

        window_name = "NIL Pumpkin Test - Saved Camera Pose"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        print("저장된 촬영 자세에서 실시간 인식을 시작합니다.")
        print("영상 창을 클릭한 뒤 Q를 누르면 정리 자세로 이동합니다.")

        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

            annotated = draw_detection(model, frame)
            cv2.imshow(window_name, annotated)

            # 실수로 다른 키를 눌러 종료하지 않도록 Q만 종료 키로 사용합니다.
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                print("종료 키가 입력되었습니다.")
                break

            # 창의 X 버튼을 눌러 닫은 경우에도 정상 종료합니다.
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("영상 창이 닫혔습니다.")
                break

    except KeyboardInterrupt:
        print("\nCtrl-C가 입력되었습니다.")

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
