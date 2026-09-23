"""Pure YOLO pumpkin-box detection helpers.

This module owns model-class validation and raw image inference only.  It does
not know about the robot, homography, scan angle, inverse kinematics, or the
gripper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


DEFAULT_TARGET_CLASS_NAMES = frozenset({"nil_pumpkin", "pumpkin"})


@dataclass(frozen=True)
class PumpkinBox:
    """One accepted YOLO pumpkin box in image coordinates."""

    xyxy: tuple[float, float, float, float]
    confidence: float
    class_id: int
    class_name: str

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.xyxy
        return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def normalize_name(value: object) -> str:
    return str(value).strip().lower()


def _class_name(model: Any, class_id: int) -> str:
    names = model.names
    if isinstance(names, dict):
        return normalize_name(names[class_id])
    return normalize_name(names[class_id])


def _normalized_targets(target_names: Iterable[str]) -> frozenset[str]:
    return frozenset(normalize_name(name) for name in target_names)


def validate_model(
    model: Any,
    target_names: Iterable[str] = DEFAULT_TARGET_CLASS_NAMES,
) -> None:
    """Ensure that the loaded model contains a supported pumpkin class."""

    names = model.names.values() if isinstance(model.names, dict) else model.names
    available = {normalize_name(name) for name in names}
    required = _normalized_targets(target_names)
    if not available.intersection(required):
        expected = " 또는 ".join(sorted(required))
        raise ValueError(
            f"모델 클래스에 {expected}이(가) 없습니다: {model.names}"
        )


def detect_pumpkin_boxes(
    model: Any,
    frame: np.ndarray,
    *,
    confidence: float,
    image_size: int,
    target_names: Iterable[str] = DEFAULT_TARGET_CLASS_NAMES,
    device: str = "cpu",
) -> tuple[Any, list[PumpkinBox]]:
    """Run YOLO once and return only accepted pumpkin boxes.

    The returned Ultralytics result is preserved for callers that need its
    plotting facilities.  All coordinates and confidences are copied to plain
    Python values so downstream code no longer depends on tensor objects.
    """

    result = model.predict(
        source=frame,
        conf=float(confidence),
        imgsz=int(image_size),
        device=device,
        verbose=False,
    )[0]
    accepted = _normalized_targets(target_names)
    detections: list[PumpkinBox] = []

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = _class_name(model, class_id)
        if class_name not in accepted:
            continue
        xyxy = tuple(float(value) for value in box.xyxy[0].tolist())
        if len(xyxy) != 4 or not np.all(np.isfinite(xyxy)):
            continue
        confidence_value = float(box.conf[0].item())
        if not np.isfinite(confidence_value):
            continue
        detections.append(
            PumpkinBox(
                xyxy=xyxy,
                confidence=confidence_value,
                class_id=class_id,
                class_name=class_name,
            )
        )

    return result, detections
