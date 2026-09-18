"""Hold OMX joint1 at +100 degrees and test nil_pumpkin.pt live detection.

Click the video window and press any key to stop. The arm moves to park in the
finally block before disconnecting.
"""

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
CAMERA_INDEX = 0
CONFIDENCE = 0.25
YOLO_IMAGE_SIZE = 416

TARGET_JOINT1_DEG = 100.0  # ready 기준 오프셋이 아닌 joint1 절대각도
MOVE_DURATION_SEC = 6.0


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
        "Joint1 fixed at +100 deg",
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
        "Press any key to park and exit",
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

        print(f"YOLO 모델을 불러옵니다: {MODEL_PATH}")
        model = YOLO(str(MODEL_PATH))
        print("YOLO 클래스:", model.names)

        cap = open_camera()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        target_joints = arm.joints().copy()
        target_joints[0] = np.radians(TARGET_JOINT1_DEG)

        print(f"joint1을 절대각도 {TARGET_JOINT1_DEG:+.1f}도로 이동합니다.")
        arm.move_joints(target_joints, duration=MOVE_DURATION_SEC)
        time.sleep(0.7)

        window_name = "NIL Pumpkin Test - Joint1 +100 deg"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        print("+100도에서 실시간 인식을 시작합니다.")
        print("영상 창을 클릭한 뒤 아무 키나 누르면 정리 자세로 이동합니다.")

        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

            annotated = draw_detection(model, frame)
            cv2.imshow(window_name, annotated)

            # 영상 창에서 어떤 키든 누르면 종료합니다.
            if cv2.waitKey(1) != -1:
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
