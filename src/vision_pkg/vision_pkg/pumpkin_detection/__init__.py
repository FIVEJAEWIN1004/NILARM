"""호박 검출 및 색상 판별 모듈."""

from .color_classifier import (
    body_region,
    clamp_box,
    classify_pumpkin_hsv,
    label_color,
)

__all__ = [
    "body_region",
    "clamp_box",
    "classify_pumpkin_hsv",
    "label_color",
]
