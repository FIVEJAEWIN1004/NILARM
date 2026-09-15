import cv2
import matplotlib.pyplot as plt


CAM = 0  # /dev/video0 카메라

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

# 오래된 프레임이 나오지 않도록 설정
cap.set(
    cv2.CAP_PROP_BUFFERSIZE,
    1
)

# 카메라 워밍업
for _ in range(5):
    cap.read()

# 사진 한 장 촬영
ok, frame = cap.read()

cap.release()

if not ok or frame is None:
    print("카메라 영상을 읽지 못했습니다.")

else:
    print(
        "카메라",
        CAM,
        "해상도",
        frame.shape[1],
        "x",
        frame.shape[0]
    )

    # OpenCV는 BGR, matplotlib은 RGB라서 색상 순서 변경
    frame_rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    plt.figure(figsize=(9, 5))
    plt.imshow(frame_rgb)
    plt.axis("off")
    plt.show()