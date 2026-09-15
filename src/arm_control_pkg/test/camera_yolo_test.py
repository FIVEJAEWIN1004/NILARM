import cv2
from ultralytics import YOLO


# ==========================================
# 설정
# ==========================================

CAM = 0

# best.pt의 실제 경로로 수정
MODEL_PATH = "/home/chaeyoung/KSAM/NILARM/src/vision_pkg/models/pumpkin_best.pt"

CONFIDENCE = 0.5


# ==========================================
# YOLO 모델 불러오기
# ==========================================

model = YOLO(MODEL_PATH)

print("YOLO 클래스:", model.names)


# ==========================================
# 카메라 연결
# ==========================================

cap = cv2.VideoCapture(
    CAM,
    cv2.CAP_V4L2
)

cap.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*"MJPG")
)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)

cap.set(
    cv2.CAP_PROP_BUFFERSIZE,
    1
)


if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    raise SystemExit


print("실시간 호박 인식을 시작합니다.")
print("영상 창에서 q를 누르면 종료됩니다.")


# ==========================================
# 실시간 인식
# ==========================================

while True:
    ok, frame = cap.read()

    if not ok or frame is None:
        print("카메라 영상을 읽지 못했습니다.")
        break

    # 현재 영상 한 프레임에 YOLO 적용
    results = model.predict(
        source=frame,
        conf=CONFIDENCE,
        verbose=False
    )

    result = results[0]

    orange_count = 0
    green_count = 0

    # 인식된 객체 확인
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())

        class_name = str(
            model.names[class_id]
        ).lower()

        # 실제 모델의 클래스명에 맞게 수정할 수 있음
        if class_name in [
            "orange",
            "orange_pumpkin",
            "ripe"
        ]:
            orange_count += 1

        elif class_name in [
            "green",
            "green_pumpkin",
            "unripe"
        ]:
            green_count += 1

        print(
            "인식:",
            class_name,
            "신뢰도:",
            round(confidence, 2)
        )

    # YOLO가 박스와 이름을 그려준 영상
    annotated_frame = result.plot()

    # 화면에 호박 개수 표시
    cv2.putText(
        annotated_frame,
        f"Orange: {orange_count}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 165, 255),
        3
    )

    cv2.putText(
        annotated_frame,
        f"Green: {green_count}",
        (30, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 255, 0),
        3
    )

    cv2.imshow(
        "Pumpkin Detection",
        annotated_frame
    )

    # 영상 창을 선택한 뒤 q를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==========================================
# 종료
# ==========================================

cap.release()
cv2.destroyAllWindows()

print("카메라와 YOLO를 종료했습니다.")