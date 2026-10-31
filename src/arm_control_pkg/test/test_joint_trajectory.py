"""Continuous multi-waypoint joint trajectory tests without hardware."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import joint_trajectory as trajectory

HZ = 100.0


@pytest.fixture(autouse=True)
def no_stream_sleep(monkeypatch):
    monkeypatch.setattr(
        trajectory, "stream",
        lambda path, write, _hz: [write(point) for point in path] and 0)


class StreamArm:
    hz = HZ

    def __init__(self, start, fail_at=None, bad_target=None):
        self.start = np.radians(start)
        self.points = []
        self.fail_at = fail_at
        self.bad_target = bad_target

    def joints(self):
        return self.start

    def check_limits(self, q, _current=None):
        if self.bad_target is not None and np.allclose(q, self.bad_target):
            raise ValueError("soft limit")
        return np.asarray(q, dtype=float)

    def _write(self, q):
        if self.fail_at is not None and len(self.points) == self.fail_at:
            raise RuntimeError("bus error")
        self.points.append(np.asarray(q, dtype=float))


def deg(*values):
    return np.radians(np.asarray(values, dtype=float))


def speeds_dps(points, start):
    path = np.degrees(np.asarray([start] + points))
    velocity = np.diff(path, axis=0) * HZ
    return velocity, np.diff(velocity, axis=0) * HZ


def test_blends_same_direction_and_stops_reversing_joint():
    arm = StreamArm([0, 0])
    a, b = deg(10, 10), deg(20, 0)  # joint 1 continues, joint 2 reverses

    trajectory.move_joints_continuous(arm, [(a, 1.0), (b, 1.0)], [21.9])

    np.testing.assert_array_equal(arm.points[99], a)
    np.testing.assert_array_equal(arm.points[-1], b)
    knot = np.degrees(arm.points[100] - arm.points[98]) * HZ / 2.0
    assert knot[0] == pytest.approx(10.0, abs=0.05)  # min(10, 10) deg/s
    assert abs(knot[1]) < 0.05
    velocity, accel = speeds_dps(arm.points, arm.start)
    assert np.max(np.abs(velocity)) <= trajectory.MAX_JOINT_SPEED_DPS
    assert np.max(np.abs(accel)) <= trajectory.MAX_JOINT_ACCEL_DPS2
    # C1/C2: velocity continuous and acceleration ~0 across the waypoint.
    assert np.max(np.abs(velocity[100] - velocity[99])) < 0.1
    assert np.max(np.abs(accel[98:101])) < 10.0
    # Joint 2 never overshoots 10 deg; final point is at rest.
    assert np.max(np.degrees(np.asarray(arm.points)[:, 1])) <= 10.0 + 1e-9
    assert np.max(np.abs(velocity[-1])) < 0.05


def test_zero_cap_is_a_full_stop_and_matches_rest_to_rest():
    arm = StreamArm([0])
    trajectory.move_joints_continuous(arm, [(deg(10), 1.0), (deg(20), 1.0)], [0.0])

    assert abs(np.degrees(arm.points[100] - arm.points[98])[0]) < 0.05
    from omx_f.trajectory import quintic
    expected = np.radians(10.0 * quintic(0.5))
    assert arm.points[49][0] == pytest.approx(expected)


def test_durations_round_up_to_whole_periods_so_waypoints_are_written():
    arm = StreamArm([0])
    trajectory.move_joints_continuous(
        arm, [(deg(5), 0.333), (deg(9), 0.401)], [21.9])

    assert len(arm.points) == 34 + 41
    np.testing.assert_array_equal(arm.points[33], deg(5))
    np.testing.assert_array_equal(arm.points[-1], deg(9))


def test_too_fast_plan_is_rejected_before_any_write():
    arm = StreamArm([0])
    with pytest.raises(ValueError):
        trajectory.move_joints_continuous(arm, [(deg(90), 1.0)], [])
    assert arm.points == []


def test_limit_error_is_raised_before_any_write():
    arm = StreamArm([0], bad_target=deg(20))
    with pytest.raises(ValueError):
        trajectory.move_joints_continuous(
            arm, [(deg(10), 1.0), (deg(20), 1.0)], [21.9])
    assert arm.points == []


def test_write_error_stops_streaming_immediately():
    arm = StreamArm([0], fail_at=30)
    with pytest.raises(RuntimeError):
        trajectory.move_joints_continuous(
            arm, [(deg(10), 1.0), (deg(20), 1.0)], [21.9])
    assert len(arm.points) == 30


def test_waypoint_count_must_match_caps():
    with pytest.raises(ValueError):
        trajectory.move_joints_continuous(StreamArm([0]), [(deg(1), 1.0)], [5.0])
