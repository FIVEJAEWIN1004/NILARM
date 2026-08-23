import cv2
import numpy as np


class HSVDetector:

    def __init__(self, min_area=500):
        self.min_area = min_area

    def detect_red(self, frame):

        # BGR 이미지를 HSV 이미지로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 빨간색은 HSV 영역의 양 끝에 걸쳐 있어서
        # 두 구간을 사용해야 함
        lower_red1 = np.array([0, 100, 80])
        upper_red1 = np.array([10, 255, 255])

        lower_red2 = np.array([170, 100, 80])
        upper_red2 = np.array([179, 255, 255])

        # 빨간색 영역 추출
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        mask = cv2.bitwise_or(mask1, mask2)

        # 작은 노이즈 제거
        kernel = np.ones((5, 5), np.uint8)

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel
        )

        # 윤곽선 찾기
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # 아무것도 검출되지 않은 경우
        if not contours:
            return None, mask

        # 가장 큰 빨간 물체 선택
        contour = max(contours, key=cv2.contourArea)

        area = cv2.contourArea(contour)

        # 너무 작은 물체는 무시
        if area < self.min_area:
            return None, mask

        # 중심점 계산
        moments = cv2.moments(contour)

        if moments["m00"] == 0:
            return None, mask

        u = int(moments["m10"] / moments["m00"])
        v = int(moments["m01"] / moments["m00"])

        # 사각형 영역
        x, y, w, h = cv2.boundingRect(contour)

        result = {
            "u": u,
            "v": v,
            "area": area,
            "bbox": (x, y, w, h)
        }

        return result, mask