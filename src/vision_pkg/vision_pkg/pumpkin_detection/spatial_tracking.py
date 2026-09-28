"""Generic 2-D nearest-neighbour matching for pumpkin observations.

The matching code is independent of robot control, scan angles, camera
access, and the payload stored in each track.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
import math
from typing import TypeVar


ItemT = TypeVar("ItemT")


def nearest_within(
    items: Iterable[ItemT],
    target_xy: Sequence[float],
    max_distance: float,
    *,
    xy_getter: Callable[[ItemT], Sequence[float]] = lambda item: (
        item.x,
        item.y,
    ),
    eligible: Callable[[ItemT], bool] | None = None,
) -> ItemT | None:
    """Return the closest eligible item within ``max_distance``."""

    if len(target_xy) != 2:
        raise ValueError("target_xy must contain exactly two coordinates")
    target_x, target_y = (float(value) for value in target_xy)
    limit = float(max_distance)
    if not math.isfinite(target_x) or not math.isfinite(target_y):
        raise ValueError("target_xy must contain finite coordinates")
    if not math.isfinite(limit) or limit < 0.0:
        raise ValueError("max_distance must be finite and non-negative")

    nearest: ItemT | None = None
    nearest_distance = float("inf")

    for item in items:
        if eligible is not None and not eligible(item):
            continue
        item_xy = xy_getter(item)
        if len(item_xy) != 2:
            continue
        item_x, item_y = (float(value) for value in item_xy)
        if not math.isfinite(item_x) or not math.isfinite(item_y):
            continue
        distance = math.hypot(item_x - target_x, item_y - target_y)
        if distance <= limit and distance < nearest_distance:
            nearest = item
            nearest_distance = distance

    return nearest
