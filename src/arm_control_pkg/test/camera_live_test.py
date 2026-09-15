import cv2


CAM = 0  # /dev/video0

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


print("실시간 영상을 시작합니다.")
print("영상 창에서 q를 누르면 종료됩니다.")

while True:
    ok, frame = cap.read()

    if not ok or frame is None:
        print("카메라 영상을 읽지 못했습니다.")
        break

    cv2.imshow(
        "OMX Camera",
        frame
    )

    # 영상 창이 선택된 상태에서 q를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()

print("카메라를 종료했습니다.")