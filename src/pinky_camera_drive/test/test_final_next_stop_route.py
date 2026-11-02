"""Non-driving tests for the post-harvest final Bezier route."""

import math
import types

import numpy as np
import pytest
import yaml

from pinky_camera_drive import camera_straight_drive as drive


Drive = drive.CameraStraightDrive


class Log:
    def __init__(self):
        self.lines = []

    def warning(self, text):
        self.lines.append(text)


class Stamp:
    def __sub__(self, other):
        return types.SimpleNamespace(nanoseconds=0)


def make_route_node():
    node = types.SimpleNamespace(
        current_x=1.2,
        current_y=-0.4,
        current_yaw=math.radians(30.0),
        next_stop_target_forward=0.26,
        next_stop_target_right=0.30,
        next_stop_target_yaw_relative=math.radians(-90.0),
        next_stop_start_handle=0.22,
        next_stop_end_handle=0.14,
        curve_sample_count=121,
        display_mode_pub=object(),
    )
    node.log = Log()
    node.get_logger = lambda: node.log
    node._publish_media = lambda *args: None
    node._normalize_angle = Drive._normalize_angle
    node._build_bezier_trajectory = Drive._build_bezier_trajectory.__get__(node)
    node._start_next_stop_from_station = (
        Drive._start_next_stop_from_station.__get__(node))
    return node


def test_next_stop_target_uses_actual_departure_odom_pose():
    node = make_route_node()
    node._start_next_stop_from_station('now')
    yaw = math.radians(30.0)
    expected_x = 1.2 + math.cos(yaw) * 0.26 + math.sin(yaw) * 0.30
    expected_y = -0.4 + math.sin(yaw) * 0.26 - math.cos(yaw) * 0.30
    assert node.station_start_x == 1.2
    assert node.station_start_y == -0.4
    assert node.station_start_yaw == yaw
    assert node.next_stop_target_x == pytest.approx(expected_x)
    assert node.next_stop_target_y == pytest.approx(expected_y)
    assert node.next_stop_target_yaw == pytest.approx(math.radians(-60.0))
    assert node.state == drive.DriveState.STATION_TO_NEXT_STOP


def test_next_stop_bezier_has_no_backward_or_target_overshoot():
    node = make_route_node()
    node.current_x = node.current_y = node.current_yaw = 0.0
    node._start_next_stop_from_station('now')
    assert np.all(np.diff(node.curve_points[:, 0]) >= -1e-12)
    assert np.all(np.diff(node.curve_points[:, 1]) <= 1e-12)
    assert node.curve_points[:, 0].min() >= 0.0
    assert node.curve_points[:, 0].max() <= 0.26
    assert node.curve_points[:, 1].min() >= -0.30
    assert node.curve_points[:, 1].max() <= 0.0


def test_finish_next_stop_goes_directly_to_final_reached_and_stops_five_times(
):
    node = types.SimpleNamespace(
        enabled=True,
        sequence_active=True,
        command_active=True,
        last_linear_command=0.05,
        steering_command=-0.1,
        current_x=0.26,
        current_y=-0.30,
        current_yaw=math.radians(-90.0),
        next_stop_target_x=0.26,
        next_stop_target_y=-0.30,
        next_stop_target_yaw=math.radians(-90.0),
        curve_distance=math.hypot(0.26, 0.30),
        next_stop_target_forward=0.28,
        next_stop_target_right=0.30,
        next_stop_target_yaw_relative=math.radians(-90.0),
        music_pub=object(),
        stops=[],
        media=[],
    )
    node.log = Log()
    node.get_logger = lambda: node.log
    node._publish_stop = lambda repeat=1: node.stops.append(repeat)
    node._publish_media = lambda publisher, text: node.media.append(text)
    node._normalize_angle = Drive._normalize_angle
    Drive._finish_next_stop(node)
    assert node.state == drive.DriveState.FINAL_REACHED
    assert not node.enabled and not node.sequence_active and not node.command_active
    assert node.last_linear_command == 0.0 and node.steering_command == 0.0
    assert node.stops == [5]
    assert node.media == ['STOP']
    assert 'forward=0.28m, right=0.30m, yaw=-90deg' in node.log.lines[-1]


def test_yaml_has_final_route_target_and_camera_speed():
    config_path = (
        __import__('pathlib').Path(__file__).resolve().parents[1]
        / 'config' / 'camera_straight_drive.yaml'
    )
    params = yaml.safe_load(config_path.read_text())['camera_straight_drive'][
        'ros__parameters']
    assert params['linear_speed'] == 0.10
    assert params['next_stop_linear_speed'] == params['linear_speed']
    assert params['next_stop_target_forward_m'] == 0.28
    assert params['next_stop_target_right_m'] == 0.30
    assert params['next_stop_target_yaw_deg'] == -90.0
    assert params['curve_linear_speed'] == 0.04


def test_next_stop_uses_camera_speed_without_changing_other_curve_speed():
    published = []
    node = types.SimpleNamespace(
        state=drive.DriveState.STATION_TO_NEXT_STOP,
        curve_started_at=Stamp(),
        station_timeout=25.0,
        station_max_travel=0.85,
        curve_distance=0.0,
        curve_target_x=1.0,
        curve_target_y=0.0,
        curve_target_yaw=0.0,
        current_x=0.0,
        current_y=0.0,
        current_yaw=0.0,
        curve_position_tolerance=0.02,
        curve_yaw_tolerance=math.radians(3.0),
        curve_points=np.array([[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]]),
        curve_progress_index=0,
        curve_arc_lengths=np.array([0.0, 0.5, 1.0]),
        curve_lookahead=0.05,
        curve_yaws=np.array([0.0, 0.0, 0.0]),
        curve_curvatures=np.array([0.0, 0.0, 0.0]),
        curve_min_linear_speed=0.015,
        curve_linear_speed=0.04,
        next_stop_linear_speed=0.05,
        curve_kp_position=1.5,
        curve_kp_yaw=0.8,
        max_angular_speed=0.15,
        next_stop_max_angular_z=0.10,
        next_stop_max_angular_accel=0.40,
        next_stop_goal_slowdown_gain=0.8,
        control_rate=20.0,
        station_overshoot_tolerance=0.01,
        steering_command=0.0,
        max_linear_speed=0.08,
        cmd_pub=types.SimpleNamespace(publish=published.append),
        command_active=False,
    )
    node._normalize_angle = Drive._normalize_angle
    Drive._control_curve(node, Stamp())
    assert published[-1].linear.x == pytest.approx(0.05)
    assert node.curve_linear_speed == 0.04


def test_final_route_geometry_and_angular_limit_are_preserved():
    node = make_route_node()
    node.current_x = node.current_y = node.current_yaw = 0.0
    node._start_next_stop_from_station('now')
    length = float(np.linalg.norm(
        np.diff(node.curve_points, axis=0), axis=1).sum())
    max_curvature = float(np.max(np.abs(node.curve_curvatures)))
    assert length == pytest.approx(0.45536, abs=1e-4)
    assert max_curvature == pytest.approx(5.158, abs=0.01)
    assert 0.05 * max_curvature > 0.10  # controller must curvature-limit speed


def test_removed_post_harvest_states_and_parameters_are_gone():
    source_path = (
        __import__('pathlib').Path(__file__).resolve().parents[1]
        / 'pinky_camera_drive' / 'camera_straight_drive.py'
    )
    source = source_path.read_text()
    config_path = source_path.parents[1] / 'config' / 'camera_straight_drive.yaml'
    config = config_path.read_text()
    removed = (
        'NEXT_STOP_FINAL_ROTATE',
        'NEXT_WAYPOINT_WAIT',
        'NEXT_WAYPOINT_MOVE',
        'FINAL_CAMERA_DRIVING',
        'FINAL_STRAIGHT_DRIVING',
        'next_stop_final_rotate_deg',
        'next_waypoint_target_forward_m',
        'final_camera_distance_m',
        'final_straight_distance_m',
    )
    assert all(name not in source for name in removed)
    assert all(name not in config for name in removed)


def test_next_stop_turns_faster_than_route_angular_limit():
    published = []
    node = types.SimpleNamespace(
        state=drive.DriveState.STATION_TO_NEXT_STOP,
        curve_started_at=Stamp(),
        station_timeout=25.0,
        station_max_travel=0.85,
        curve_distance=0.0,
        curve_target_x=0.26,
        curve_target_y=-0.30,
        curve_target_yaw=-math.pi / 2.0,
        current_x=0.0,
        current_y=0.0,
        current_yaw=0.0,
        curve_position_tolerance=0.02,
        curve_yaw_tolerance=math.radians(3.0),
        curve_points=np.array([[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]]),
        curve_progress_index=0,
        curve_arc_lengths=np.array([0.0, 0.5, 1.0]),
        curve_lookahead=0.05,
        curve_yaws=np.array([0.0, 0.0, 0.0]),
        curve_curvatures=np.array([-5.0, -5.0, -5.0]),
        curve_min_linear_speed=0.015,
        curve_linear_speed=0.04,
        next_stop_linear_speed=0.10,
        curve_kp_position=0.0,
        curve_kp_yaw=0.0,
        max_angular_speed=0.15,
        next_stop_max_angular_z=0.50,
        next_stop_max_angular_accel=100.0,
        next_stop_goal_slowdown_gain=1.5,
        control_rate=20.0,
        station_overshoot_tolerance=0.01,
        steering_command=0.0,
        max_linear_speed=0.10,
        cmd_pub=types.SimpleNamespace(publish=published.append),
        command_active=False,
    )
    node._normalize_angle = Drive._normalize_angle
    Drive._control_curve(node, Stamp())
    assert published[-1].linear.x == pytest.approx(0.10)
    assert published[-1].angular.z == pytest.approx(-0.50)
