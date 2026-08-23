import cv2

from vision_pkg.hsv_detector import HSVDetector


detector = HSVDetector()

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()


while True:

    ret, frame = cap.read()

    if not ret:
        break

    result, mask = detector.detect_red(frame)

    if result is not None:

        u = result["u"]
        v = result["v"]

        x, y, w, h = result["bbox"]

        # 검출된 물체에 사각형 표시
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        # 중심점 표시
        cv2.circle(
            frame,
            (u, v),
            5,
            (255, 0, 0),
            -1
        )

        # 좌표 표시
        cv2.putText(
            frame,
            f"({u}, {v})",
            (u + 10, v),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        print("Detected:", result)

    cv2.imshow("Camera", frame)
    cv2.imshow("Red Mask", mask)

    # q 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()