
"""Move OMX joint1 through several views and run live YOLO detection.

This is a scan/recognition test only. It does not calculate robot XYZ targets
and it does not pick anything. Press q in the video window or Ctrl-C in the
terminal to stop. The arm returns to park in the finally block.
"""

import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower


# ---------- Settings ----------
MODEL_PATH = Path(
    "/home/chaeyoung/KSAM/NILARM/src/vision_pkg/models/nil_pumpkin.pt"
)
CAMERA_INDEX = 0
CONFIDENCE = 0.25

SCAN_OFFSETS_DEG = [-140, -100, -60, -20, 20, 60, 100, 140]
MOVE_DURATION_SEC = 6.0
SETTLE_TIME_SEC = 0.7
VIEW_TIME_SEC = 2.0


def open_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"카메라 /dev/video{CAMERA_INDEX}를 열 수 없습니다.")

    for _ in range(8):
        cap.read()

    return cap


def detect_and_draw(model, frame, offset_deg):
    result = model.predict(source=frame, conf=CONFIDENCE, verbose=False)[0]
    counts = Counter()

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = str(model.names[class_id])
        counts[class_name] += 1

    # YOLO 검출 네모박스, 클래스명, 신뢰도를 자동으로 그립니다.
    annotated = result.plot()

    cv2.putText(
        annotated,
        f"Scan offset: {offset_deg:+.0f} deg",
        (25, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )

    y = 78
    for class_name, count in sorted(counts.items()):
        cv2.putText(
            annotated,
            f"{class_name}: {count}",
            (25, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )
        y += 34

    cv2.putText(
        annotated,
        "Press q to stop",
        (25, annotated.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
    )
    return annotated, counts


def show_one_scan_view(model, cap, offset_deg):
    deadline = time.monotonic() + VIEW_TIME_SEC
    maximum_counts = Counter()

    while time.monotonic() < deadline:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

        annotated, counts = detect_and_draw(model, frame, offset_deg)
        for class_name, count in counts.items():
            maximum_counts[class_name] = max(maximum_counts[class_name], count)

        cv2.imshow("OMX NIL Pumpkin Scan", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return maximum_counts, True

    return maximum_counts, False


def main():
    arm = None
    cap = None
    ready_joints = None

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"모델 파일이 없습니다: {MODEL_PATH}\n"
                "첨부한 nil_pumpkin.pt를 위 경로에 저장하세요."
            )

        print(f"YOLO 모델을 불러옵니다: {MODEL_PATH}")
        model = YOLO(str(MODEL_PATH))
        print("YOLO 클래스:", model.names)

        cap = open_camera()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        ready_joints = arm.joints().copy()
        ready_joint1_deg = float(np.degrees(ready_joints[0]))

        print("기본 관절각 [deg]:", np.round(np.degrees(ready_joints), 1))
        print("q 또는 Ctrl-C를 누르면 중단합니다.")

        view_results = []
        for offset_deg in SCAN_OFFSETS_DEG:
            target_joint1_deg = ready_joint1_deg + offset_deg

            if not -145.0 <= target_joint1_deg <= 145.0:
                print(
                    f"[건너뜀] joint1={target_joint1_deg:.1f}도: "
                    "안전 범위를 벗어났습니다."
                )
                continue

            target_joints = ready_joints.copy()
            target_joints[0] = np.radians(target_joint1_deg)

            print(
                f"[이동] 기준에서 {offset_deg:+.0f}도 "
                f"(joint1={target_joint1_deg:.1f}도)"
            )
            arm.move_joints(target_joints, duration=MOVE_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            counts, stop_requested = show_one_scan_view(model, cap, offset_deg)
            view_results.append((offset_deg, counts))
            print(f"[인식] {offset_deg:+.0f}도: {dict(counts)}")

            if stop_requested:
                break

        print("\n각 촬영 방향의 인식 결과")
        for offset_deg, counts in view_results:
            print(f"  {offset_deg:+.0f}도: {dict(counts)}")

        print(
            "주의: 같은 호박이 여러 방향에서 검출될 수 있으므로 "
            "방향별 숫자를 더해 실제 전체 개수로 사용하면 안 됩니다."
        )

    except KeyboardInterrupt:
        print("\n사용자가 스캔을 중단했습니다.")

    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if ready_joints is not None:
                    print("기본 자세로 돌아갑니다.")
                    arm.move_joints(ready_joints, duration=3.0)
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()


if __name__ == "__main__":
    main()
