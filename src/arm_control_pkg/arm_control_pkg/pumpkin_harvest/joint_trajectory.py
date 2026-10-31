"""Velocity-continuous multi-waypoint joint moves streamed through omx_f.

omx_f.move_joints() runs one rest-to-rest quintic per call, so a chain of
calls stops at every waypoint.  Here every segment is a quintic with zero
acceleration at both ends, so velocity and acceleration stay continuous
across waypoints.  Each waypoint is still reached exactly; only joints that
keep moving in the same direction pass it with a non-zero (capped) speed.
"""

from __future__ import annotations

import math

import numpy as np
from omx_f import stream

# Servo Profile Velocity 30 x 0.229 rpm and Profile Acceleration
# 10 x 214.577 rev/min^2 (omx_f.config), in deg/s and deg/s^2.
MAX_JOINT_SPEED_DPS = 41.2
MAX_JOINT_ACCEL_DPS2 = 215.0
_CHECK_SAMPLES = 400
_VIA_SCALES = (1.0, 0.5, 0.25, 0.125, 0.0)


def _coefficients(p0, p1, v0, v1, duration):
    """Quintic p(t) = sum c_k t^k with p, v given and zero end accelerations."""
    delta, t = p1 - p0, duration
    c3 = (20.0 * delta - (8.0 * v1 + 12.0 * v0) * t) / (2.0 * t**3)
    c4 = (-30.0 * delta + (14.0 * v1 + 16.0 * v0) * t) / (2.0 * t**4)
    c5 = (12.0 * delta - 6.0 * (v1 + v0) * t) / (2.0 * t**5)
    zero = np.zeros_like(p0)
    return np.stack([p0, v0, zero, c3, c4, c5])


def _evaluate(coeffs, t, order=0):
    powers = range(order, 6)
    return sum(
        coeffs[k] * (math.factorial(k) / math.factorial(k - order)) * t ** (k - order)
        for k in powers
    )


def via_velocities(points, durations, caps_dps):
    """Waypoint velocities [rad/s]: zero at both ends, at reversals and stops."""
    velocities = [np.zeros_like(points[0]) for _ in points]
    for i, cap_dps in enumerate(caps_dps, start=1):
        before = (points[i] - points[i - 1]) / durations[i - 1]
        after = (points[i + 1] - points[i]) / durations[i]
        same_direction = before * after > 0.0
        speed = np.minimum(
            np.minimum(np.abs(before), np.abs(after)), math.radians(cap_dps)
        )
        velocities[i] = np.where(same_direction, np.sign(before) * speed, 0.0)
    return velocities


def check_segment(coeffs, p0, p1, duration) -> bool:
    """Speed/acceleration limits and no overshoot past either waypoint."""
    t = np.linspace(0.0, duration, _CHECK_SAMPLES)[:, None]
    position = _evaluate(coeffs, t)
    speed = np.degrees(np.abs(_evaluate(coeffs, t, 1)))
    accel = np.degrees(np.abs(_evaluate(coeffs, t, 2)))
    low, high = np.minimum(p0, p1) - 1e-9, np.maximum(p0, p1) + 1e-9
    return bool(
        np.all(speed <= MAX_JOINT_SPEED_DPS + 1e-9)
        and np.all(accel <= MAX_JOINT_ACCEL_DPS2 + 1e-9)
        and np.all((position >= low) & (position <= high))
    )


def plan(start, targets, durations, caps_dps, hz):
    """Return (durations, via velocities, coefficients) or raise ValueError.

    Durations are rounded up to whole control periods so every waypoint is
    written exactly.  Via speeds shrink until every segment passes the checks;
    with all via speeds at zero this is the existing rest-to-rest motion.
    """
    if len(caps_dps) != len(targets) - 1:
        raise ValueError("중간 waypoint마다 연결속도 상한이 필요합니다.")
    points = [np.asarray(start, dtype=float)] + [
        np.asarray(target, dtype=float) for target in targets
    ]
    durations = [
        math.ceil(float(duration) * hz - 1e-9) / hz for duration in durations
    ]
    if min(durations) <= 0.0:
        raise ValueError("구간 시간은 0보다 커야 합니다.")
    for scale in _VIA_SCALES:
        velocities = via_velocities(
            points, durations, [cap * scale for cap in caps_dps]
        )
        segments = [
            _coefficients(points[i], points[i + 1], velocities[i],
                          velocities[i + 1], durations[i])
            for i in range(len(durations))
        ]
        if all(
            check_segment(segments[i], points[i], points[i + 1], durations[i])
            for i in range(len(durations))
        ):
            return durations, velocities, segments
    raise ValueError("연속 궤적이 관절 속도·가속도 한계를 넘습니다.")


def sample_path(targets, durations, segments, hz):
    """Yield control-period points; each waypoint is yielded exactly."""
    for target, duration, coeffs in zip(targets, durations, segments):
        steps = round(duration * hz)
        for k in range(1, steps):
            yield _evaluate(coeffs, k / hz)
        yield np.asarray(target, dtype=float)


def move_joints_continuous(arm, segments, via_speed_caps_dps) -> int:
    """Stream [(target_rad, duration_s), ...] through every target, ending at rest.

    via_speed_caps_dps[i] caps the joint speed while passing segments[i]'s
    target; 0 makes it a full stop.  Limits and the whole plan are checked
    before the first point is written.  A write error stops streaming.
    """
    current = np.asarray(arm.joints(), dtype=float)
    targets = []
    previous = current
    for target, _duration in segments:
        previous = arm.check_limits(target, previous)
        targets.append(previous)
    durations, _velocities, coeffs = plan(
        current,
        targets,
        [duration for _target, duration in segments],
        via_speed_caps_dps,
        arm.hz,
    )
    return stream(sample_path(targets, durations, coeffs, arm.hz), arm._write, arm.hz)
