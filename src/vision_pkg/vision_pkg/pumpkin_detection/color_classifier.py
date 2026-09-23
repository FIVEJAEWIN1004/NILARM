"""호박의 HSV 색상을 분류하는 순수 Vision 모듈.

로봇팔이나 카메라 장치를 직접 제어하지 않는다.
"""

from __future__ import annotations

import cv2
import numpy as np


ORANGE_HSV_LOW = np.asarray([0, 80, 45], dtype=np.uint8)
ORANGE_HSV_HIGH = np.asarray([28, 255, 255], dtype=np.uint8)
ORANGE_WRAP_HSV_LOW = np.asarray([170, 80, 45], dtype=np.uint8)
ORANGE_WRAP_HSV_HIGH = np.asarray([179, 255, 255], dtype=np.uint8)
GREEN_HSV_LOW = np.asarray([32, 55, 35], dtype=np.uint8)
GREEN_HSV_HIGH = np.asarray([95, 255, 255], dtype=np.uint8)
BODY_SIDE_CROP_FRACTION = 0.14
BODY_TOP_CROP_FRACTION = 0.22
BODY_BOTTOM_CROP_FRACTION = 0.06
MIN_CLASS_RATIO = 0.22
WINNER_MARGIN = 1.25
MIN_BODY_SIZE_PX = 12

def clamp_box(box, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = (float(value) for value in box)
    return (max(0, min(width - 1, int(round(x1)))), max(0, min(height - 1, int(round(y1)))), max(0, min(width, int(round(x2)))), max(0, min(height, int(round(y2)))))

def body_region(box, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = clamp_box(box, width, height)
    box_width = max(0, x2 - x1)
    box_height = max(0, y2 - y1)
    left = x1 + int(round(box_width * BODY_SIDE_CROP_FRACTION))
    right = x2 - int(round(box_width * BODY_SIDE_CROP_FRACTION))
    top = y1 + int(round(box_height * BODY_TOP_CROP_FRACTION))
    bottom = y2 - int(round(box_height * BODY_BOTTOM_CROP_FRACTION))
    return (left, top, right, bottom)

def classify_pumpkin_hsv(frame: np.ndarray, box) -> dict:
    """Classify one YOLO box from its cropped elliptical body region."""
    height, width = frame.shape[:2]
    left, top, right, bottom = body_region(box, width, height)
    roi_width = right - left
    roi_height = bottom - top
    if roi_width < MIN_BODY_SIZE_PX or roi_height < MIN_BODY_SIZE_PX:
        return {'label': 'UNKNOWN', 'orange_ratio': 0.0, 'green_ratio': 0.0, 'median_hue': None, 'body_box': (left, top, right, bottom)}
    roi = frame[top:bottom, left:right]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    ellipse = np.zeros((roi_height, roi_width), dtype=np.uint8)
    center = (roi_width // 2, roi_height // 2)
    axes = (max(1, int(round(roi_width * 0.48))), max(1, int(round(roi_height * 0.48))))
    cv2.ellipse(ellipse, center, axes, 0, 0, 360, 255, -1)
    orange_mask_low = cv2.inRange(hsv, ORANGE_HSV_LOW, ORANGE_HSV_HIGH)
    orange_mask_wrap = cv2.inRange(hsv, ORANGE_WRAP_HSV_LOW, ORANGE_WRAP_HSV_HIGH)
    orange_mask = cv2.bitwise_or(orange_mask_low, orange_mask_wrap)
    green_mask = cv2.inRange(hsv, GREEN_HSV_LOW, GREEN_HSV_HIGH)
    orange_mask = cv2.bitwise_and(orange_mask, ellipse)
    green_mask = cv2.bitwise_and(green_mask, ellipse)
    body_pixels = max(1, int(cv2.countNonZero(ellipse)))
    orange_ratio = float(cv2.countNonZero(orange_mask)) / body_pixels
    green_ratio = float(cv2.countNonZero(green_mask)) / body_pixels
    chromatic = (hsv[:, :, 1] >= 55) & (hsv[:, :, 2] >= 35) & (ellipse > 0)
    median_hue = float(np.median(hsv[:, :, 0][chromatic])) if np.any(chromatic) else None
    if orange_ratio >= MIN_CLASS_RATIO and orange_ratio >= green_ratio * WINNER_MARGIN:
        label = 'ORANGE'
    elif green_ratio >= MIN_CLASS_RATIO and green_ratio >= orange_ratio * WINNER_MARGIN:
        label = 'GREEN'
    else:
        label = 'UNKNOWN'
    return {'label': label, 'orange_ratio': orange_ratio, 'green_ratio': green_ratio, 'median_hue': median_hue, 'body_box': (left, top, right, bottom)}

def label_color(label: str) -> tuple[int, int, int]:
    if label == 'ORANGE':
        return (0, 140, 255)
    if label == 'GREEN':
        return (0, 255, 0)
    return (180, 180, 180)
