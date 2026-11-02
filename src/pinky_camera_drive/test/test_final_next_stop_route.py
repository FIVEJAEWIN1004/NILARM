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
        next_stop2_target_forward=0.13,
        next_stop2_target_right=0.13,
        next_stop2_target_yaw_relative=math.radians(-90.0),
        next_stop2_start_handle=0.072,
        next_stop2_end_handle=0.072,
        next_stop_wait_sec=3.5,
        curve_sample_count=121,
        display_mode_pub=object(),
    )
    node.log = Log()
    node.get_logger = lambda: node.log
    node.media = []
    node._publish_media = lambda publisher, text: node.media.append(text)
    node._normalize_angle = Drive._normalize_angle
    node._build_bezier_trajectory = Drive._build_bezier_trajectory.__get__(node)
    for name in ('_start_next_stop_from_station', '_start_next_stop_leg',
                 '_next_stop_leg_params', '_finish_next_stop',
                 '_control_next_stop_wait'):
        setattr(node, name, getattr(Drive, name).__get__(node))
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


class Clock:
    def __init__(self, seconds):
        self.seconds = seconds

    def now(self):
        return self

    def __sub__(self, other):
        return types.SimpleNamespace(
            nanoseconds=int((self.seconds - other.seconds) * 1e9))


def test_ninth_stop_waits_then_runs_second_curve_from_actual_pose():
    node = make_route_node()
    node.current_x = node.current_y = node.current_yaw = 0.0
    node.enabled = node.sequence_active = True
    node.stops = []
    node._publish_stop = lambda repeat=1: node.stops.append(repeat)
    clock = Clock(10.0)
    node.get_clock = lambda: clock
    node._start_next_stop_from_station(clock)
    node.curve_distance = 0.4
    node.current_x, node.current_y = 0.29, -0.29
    node.current_yaw = math.radians(-90.0)
    node._finish_next_stop()
    assert node.state == drive.DriveState.NEXT_STOP_WAIT
    assert node.enabled and node.sequence_active
    assert node.stops == [5]

    node._control_next_stop_wait(Clock(13.4))
    assert node.state == drive.DriveState.NEXT_STOP_WAIT
    node._control_next_stop_wait(Clock(13.5))
    assert node.state == drive.DriveState.STATION_TO_NEXT_STOP
    assert node.next_stop_leg == 2
    # LCD keeps the harvest result: no IMAGE switch on ⑨ or ⑩ departure.
    assert node.media == []
    # Facing -90deg: forward 0.13 is -y, right 0.13 is -x.
    assert node.next_stop_target_x == pytest.approx(0.29 - 0.13)
    assert node.next_stop_target_y == pytest.approx(-0.29 - 0.13)
    assert abs(node.next_stop_target_yaw) == pytest.approx(math.pi)
    assert node.curve_points[:, 0].min() >= 0.16 - 1e-9
    assert node.curve_points[:, 1].min() >= -0.42 - 1e-9


def test_tenth_stop_starts_final_camera_drive_from_actual_pose(
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
        next_stop_target_forward=0.29,
        next_stop_target_right=0.29,
        next_stop_target_yaw_relative=math.radians(-90.0),
        next_stop2_target_forward=0.13,
        next_stop2_target_right=0.13,
        next_stop2_target_yaw_relative=math.radians(-90.0),
        next_stop2_start_handle=0.072,
        next_stop2_end_handle=0.072,
        next_stop_leg=2,
        music_pub=object(),
        stops=[],
        media=[],
    )
    node.log = Log()
    node.get_logger = lambda: node.log
    node._publish_stop = lambda repeat=1: node.stops.append(repeat)
    node._publish_media = lambda publisher, text: node.media.append(text)
    node._normalize_angle = Drive._normalize_angle
    node._next_stop_leg_params = Drive._next_stop_leg_params.__get__(node)
    node.get_clock = lambda: Clock(20.0)
    node.target_x_config = 320.0
    node.final_camera_distance_target = 0.45
    node.final_camera_linear_speed = 0.15
    for name in ('_start_final_camera_drive', '_clear_detection'):
        setattr(node, name, getattr(Drive, name).__get__(node))
    Drive._finish_next_stop(node)
    assert node.state == drive.DriveState.FINAL_CAMERA_DRIVING
    assert node.enabled and node.sequence_active and not node.command_active
    assert node.last_linear_command == 0.0 and node.steering_command == 0.0
    assert not node.path_detected  # waits for a fresh line fit
    assert (node.final_camera_start_x, node.final_camera_start_y) == (0.26, -0.30)
    assert 'forward=0.13m, right=0.13m, yaw=-90deg' in node.log.lines[-2]


def make_final_camera_node(path_detected=True, elapsed=0.0):
    published = []
    node = types.SimpleNamespace(
        state=drive.DriveState.FINAL_CAMERA_DRIVING,
        path_detected=path_detected,
        steering_command=0.07,
        final_camera_started_at=Clock(0.0),
        final_camera_detect_timeout=1.0,
        final_camera_linear_speed=0.15,
        linear_speed=0.10,
        max_linear_speed=0.10,
        last_frame_time=Clock(elapsed),
        frame_timeout=0.5,
        command_active=True,
        cmd_pub=types.SimpleNamespace(publish=published.append),
        stops=[],
        faults=[],
    )
    node.published = published
    node._publish_stop = lambda repeat=1: node.stops.append(repeat)
    node._enter_fault = node.faults.append
    node._is_stale = lambda now, stamp, timeout: False
    node._control_camera_drive = Drive._control_camera_drive.__get__(node)
    return node


def test_final_camera_drives_at_one_and_half_times_camera_speed():
    node = make_final_camera_node()
    Drive._control_final_camera_drive(node, Clock(0.1))
    assert node.published[-1].linear.x == pytest.approx(0.15)
    assert node.published[-1].angular.z == pytest.approx(0.07)
    assert node.faults == []


def test_final_camera_waits_for_line_then_faults_after_timeout():
    node = make_final_camera_node(path_detected=False)
    Drive._control_final_camera_drive(node, Clock(0.5))
    assert node.stops == [1] and node.published == [] and node.faults == []
    Drive._control_final_camera_drive(node, Clock(1.0))
    assert node.faults == ['yellow boundary unavailable']


def test_final_camera_starts_straight_at_target_distance():
    node = types.SimpleNamespace(
        state=drive.DriveState.FINAL_CAMERA_DRIVING,
        final_camera_start_x=1.0,
        final_camera_start_y=2.0,
        final_camera_distance_target=0.45,
        finished=[],
    )
    node._start_final_straight = node.finished.append
    msg = types.SimpleNamespace(pose=types.SimpleNamespace(pose=types.SimpleNamespace(
        position=types.SimpleNamespace(x=1.0, y=2.44),
        orientation=types.SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0))))
    node.get_clock = lambda: Clock(0.0)
    node._yaw_from_quaternion = Drive._yaw_from_quaternion
    Drive._odom_callback(node, msg)
    assert node.finished == []
    msg.pose.pose.position.y = 2.45
    Drive._odom_callback(node, msg)
    assert len(node.finished) == 1
    assert node.final_camera_distance == pytest.approx(0.45)


def test_yaml_has_final_route_target_and_camera_speed():
    config_path = (
        __import__('pathlib').Path(__file__).resolve().parents[1]
        / 'config' / 'camera_straight_drive.yaml'
    )
    params = yaml.safe_load(config_path.read_text())['camera_straight_drive'][
        'ros__parameters']
    assert params['linear_speed'] == 0.10
    assert params['next_stop_linear_speed'] == params['linear_speed']
    assert params['next_stop_target_forward_m'] == 0.29
    assert params['next_stop_target_right_m'] == 0.29
    assert params['next_stop_target_yaw_deg'] == -90.0
    assert params['curve_linear_speed'] == 0.04
    assert params['final_camera_distance_m'] == 0.45
    assert params['final_camera_linear_speed'] == 0.20
    assert params['final_straight_distance_m'] == 0.45
    assert params['final_straight_linear_speed'] == params[
        'final_camera_linear_speed']


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
        'next_stop_final_rotate_deg',
        'next_waypoint_target_forward_m',
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


def make_final_straight_node():
    published = []
    node = types.SimpleNamespace(
        state=drive.DriveState.FINAL_STRAIGHT_DRIVING,
        final_straight_started_at=Clock(0.0),
        final_straight_timeout=8.0,
        final_straight_start_yaw=0.0,
        final_straight_linear_speed=0.15,
        current_yaw=0.1,
        curve_kp_yaw=0.8,
        max_angular_speed=0.15,
        cmd_pub=types.SimpleNamespace(publish=published.append),
        faults=[],
    )
    node.published = published
    node._normalize_angle = Drive._normalize_angle
    node._enter_fault = node.faults.append
    return node


def test_final_straight_holds_heading_at_camera_speed():
    node = make_final_straight_node()
    Drive._control_final_straight(node, Clock(1.0))
    assert node.published[-1].linear.x == pytest.approx(0.15)
    assert node.published[-1].angular.z == pytest.approx(-0.08)
    Drive._control_final_straight(node, Clock(8.0))
    assert node.faults == ['final straight timeout']


def test_final_straight_stops_at_target_distance():
    node = types.SimpleNamespace(
        state=drive.DriveState.FINAL_STRAIGHT_DRIVING,
        final_straight_start_x=1.0,
        final_straight_start_y=2.0,
        final_straight_distance_target=0.45,
        finished=[],
    )
    node._finish_final = node.finished.append
    msg = types.SimpleNamespace(pose=types.SimpleNamespace(pose=types.SimpleNamespace(
        position=types.SimpleNamespace(x=1.44, y=2.0),
        orientation=types.SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0))))
    node.get_clock = lambda: Clock(0.0)
    node._yaw_from_quaternion = Drive._yaw_from_quaternion
    Drive._odom_callback(node, msg)
    assert node.finished == []
    msg.pose.pose.position.x = 1.451
    Drive._odom_callback(node, msg)
    assert len(node.finished) == 1 and '0.451m' in node.finished[0]
