"""Follow a calibrated offset from a yellow boundary for a fixed odom distance."""

import math
import select
import sys
import threading

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from interfaces_pkg.action import Harvest
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
from std_srvs.srv import SetBool


class DriveState:
    DISABLED = 'DISABLED'
    CAMERA_DRIVING = 'CAMERA_DRIVING'
    TARGET_81CM_REACHED = 'TARGET_81CM_REACHED'
    CURVE_TO_FIRST_POINT = 'CURVE_TO_FIRST_POINT'
    FIRST_POINT_REACHED = 'FIRST_POINT_REACHED'
    STATION_WAIT = 'STATION_WAIT'
    TEST_FORWARD_MOVE = 'TEST_FORWARD_MOVE'
    TEST_FORWARD_REACHED = 'TEST_FORWARD_REACHED'
    WAYPOINT_TEST_FORWARD = 'WAYPOINT_TEST_FORWARD'
    WAYPOINT_TEST_ROTATE = 'WAYPOINT_TEST_ROTATE'
    WAYPOINT_SETTLE = 'WAYPOINT_SETTLE'
    WAYPOINT_TEST_REACHED = 'WAYPOINT_TEST_REACHED'
    WAYPOINT_FORWARD_ONLY_REACHED = 'WAYPOINT_FORWARD_ONLY_REACHED'
    WAYPOINT_FORWARD_ROTATE_TEST_REACHED = 'WAYPOINT_FORWARD_ROTATE_TEST_REACHED'
    WAYPOINT_REACHED = 'WAYPOINT_REACHED'
    STATION_TO_WAYPOINT = 'STATION_TO_WAYPOINT'
    STATION_WAYPOINT_REACHED = 'STATION_WAYPOINT_REACHED'
    STATION_MOVE = 'STATION_MOVE'
    STATION_MOVE_FROM_WAYPOINT = 'STATION_MOVE_FROM_WAYPOINT'
    STATION_FINAL_APPROACH = 'STATION_FINAL_APPROACH'
    STATION_REACHED = 'STATION_REACHED'
    STATION_LOAD_WAIT = 'STATION_LOAD_WAIT'
    STATION_TO_NEXT_STOP = 'STATION_TO_NEXT_STOP'
    NEXT_STOP_FINAL_ROTATE = 'NEXT_STOP_FINAL_ROTATE'
    NEXT_STOP_REACHED = 'NEXT_STOP_REACHED'
    NEXT_WAYPOINT_WAIT = 'NEXT_WAYPOINT_WAIT'
    NEXT_WAYPOINT_MOVE = 'NEXT_WAYPOINT_MOVE'
    NEXT_WAYPOINT_REACHED = 'NEXT_WAYPOINT_REACHED'
    FINAL_CAMERA_DRIVING = 'FINAL_CAMERA_DRIVING'
    FINAL_STRAIGHT_DRIVING = 'FINAL_STRAIGHT_DRIVING'
    FINAL_REACHED = 'FINAL_REACHED'
    FAULT = 'FAULT'


class CameraStraightDrive(Node):
    """Follow the left yellow boundary only after explicit service enable."""

    def __init__(self):
        super().__init__('camera_straight_drive')
        self.declare_parameter('camera_topic', '/camera/image/compressed')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('linear_speed', 0.05)
        self.declare_parameter('max_linear_speed', 0.08)
        self.declare_parameter('max_angular_speed', 0.15)
        self.declare_parameter('kp', 0.002)
        self.declare_parameter('steering_sign', -1.0)
        self.declare_parameter('target_distance_m', 0.84)
        self.declare_parameter('curve_target_x_m', 0.22)
        self.declare_parameter('curve_target_y_m', -0.19)
        self.declare_parameter('curve_target_yaw_deg', -60.0)
        self.declare_parameter('curve_position_tolerance_m', 0.02)
        self.declare_parameter('curve_yaw_tolerance_deg', 3.0)
        self.declare_parameter('curve_linear_speed', 0.04)
        self.declare_parameter('curve_min_linear_speed', 0.015)
        self.declare_parameter('curve_kp_position', 1.5)
        self.declare_parameter('curve_kp_yaw', 0.8)
        self.declare_parameter('curve_start_handle_m', 0.13)
        self.declare_parameter('curve_end_handle_m', 0.09)
        self.declare_parameter('curve_lookahead_m', 0.05)
        self.declare_parameter('curve_sample_count', 121)
        self.declare_parameter('curve_timeout_sec', 20.0)
        self.declare_parameter('curve_max_travel_m', 0.70)
        self.declare_parameter('station_stop_duration_sec', 3.5)
        self.declare_parameter('test_forward_mode', True)
        self.declare_parameter('test_forward_distance_m', 0.08)
        self.declare_parameter('test_forward_speed', 0.04)
        self.declare_parameter('test_forward_timeout_sec', 5.0)
        self.declare_parameter('test_forward_max_travel_m', 0.12)
        self.declare_parameter('station_target_forward_m', 0.31)
        self.declare_parameter('station_target_right_m', 0.18)
        self.declare_parameter('station_target_yaw_deg', -70.0)
        self.declare_parameter('station_direct_mode', False)
        self.declare_parameter('waypoint_station_mode', False)
        self.declare_parameter('station_direct_start_handle_m', 0.15)
        self.declare_parameter('station_direct_end_handle_m', 0.10)
        self.declare_parameter('station_waypoint_forward_m', 0.17)
        self.declare_parameter('station_waypoint_right_m', 0.00)
        self.declare_parameter('station_waypoint_yaw_deg', -25.0)
        self.declare_parameter('station_waypoint_test_mode', False)
        self.declare_parameter('waypoint_forward_only_test_mode', False)
        self.declare_parameter('waypoint_forward_rotate_test_mode', False)
        self.declare_parameter('waypoint_forward_rotate_test_distance_m', 0.10)
        self.declare_parameter('waypoint_forward_rotate_test_angle_deg', 45.0)
        self.declare_parameter('waypoint_forward_rotate_test_max_deg', 50.0)
        self.declare_parameter('waypoint_test_forward_distance_m', 0.10)
        self.declare_parameter('waypoint_test_forward_speed', 0.04)
        self.declare_parameter('waypoint_test_forward_timeout_sec', 8.0)
        self.declare_parameter('waypoint_test_forward_max_travel_m', 0.22)
        self.declare_parameter('waypoint_test_rotate_deg', 45.0)
        self.declare_parameter('waypoint_test_rotate_speed', 0.15)
        self.declare_parameter('waypoint_test_rotate_timeout_sec', 8.0)
        self.declare_parameter('waypoint_test_rotate_max_deg', 50.0)
        self.declare_parameter('waypoint_pose_settle_sec', 0.5)
        self.declare_parameter('station_waypoint_position_tolerance_m', 0.02)
        self.declare_parameter('station_waypoint_yaw_tolerance_deg', 3.0)
        self.declare_parameter('station_waypoint_start_handle_m', 0.081)
        self.declare_parameter('station_waypoint_end_handle_m', 0.051)
        self.declare_parameter('station_waypoint_timeout_sec', 12.0)
        self.declare_parameter('station_waypoint_max_travel_m', 0.30)
        self.declare_parameter('station_start_handle_m', 0.16)
        self.declare_parameter('station_end_handle_m', 0.08)
        self.declare_parameter('station_overshoot_tolerance_m', 0.01)
        self.declare_parameter('station_final_approach_max_m', 0.20)
        self.declare_parameter('station_final_approach_enabled', True)
        self.declare_parameter('station_final_approach_timeout_sec', 10.0)
        self.declare_parameter('station_final_approach_speed', 0.015)
        self.declare_parameter('station_final_approach_max_angular', 0.05)
        self.declare_parameter('station_timeout_sec', 25.0)
        self.declare_parameter('station_max_travel_m', 0.85)
        self.declare_parameter('manual_station_departure', True)
        self.declare_parameter('use_harvest_action', True)
        self.declare_parameter('harvest_target_count', 1)
        self.declare_parameter('next_stop_target_forward_m', 0.19)
        self.declare_parameter('next_stop_target_right_m', 0.36)
        self.declare_parameter('next_stop_target_yaw_deg', -45.0)
        self.declare_parameter('next_stop_start_handle_m', 0.22)
        self.declare_parameter('next_stop_end_handle_m', 0.14)
        self.declare_parameter('next_stop_max_angular_z', 0.10)
        self.declare_parameter('next_stop_max_angular_accel', 0.40)
        self.declare_parameter('next_stop_final_rotate_deg', 30.0)
        self.declare_parameter('next_stop_final_rotate_speed', 0.15)
        self.declare_parameter('next_stop_final_rotate_timeout_sec', 8.0)
        self.declare_parameter('next_stop_final_rotate_max_deg', 35.0)
        self.declare_parameter('next_waypoint_wait_sec', 3.5)
        self.declare_parameter('next_waypoint_target_forward_m', 0.18)
        self.declare_parameter('next_waypoint_target_right_m', 0.17)
        self.declare_parameter('next_waypoint_target_yaw_deg', -80.0)
        self.declare_parameter('next_waypoint_start_handle_m', 0.10)
        self.declare_parameter('next_waypoint_end_handle_m', 0.07)
        self.declare_parameter('final_camera_distance_m', 0.60)
        self.declare_parameter('final_straight_distance_m', 0.33)
        self.declare_parameter('final_straight_timeout_sec', 10.0)
        self.declare_parameter('final_straight_max_travel_m', 0.40)
        self.declare_parameter('target_x', 320.0)
        self.declare_parameter('boundary_reference_x', 23.0)
        self.declare_parameter('boundary_eval_y_ratio', 0.80)
        self.declare_parameter('roi_top_ratio', 0.65)
        self.declare_parameter('roi_left_ratio', 0.0)
        self.declare_parameter('roi_right_ratio', 0.70)
        self.declare_parameter('yellow_h_low', 22)
        self.declare_parameter('yellow_h_high', 35)
        self.declare_parameter('yellow_s_low', 100)
        self.declare_parameter('yellow_s_high', 190)
        self.declare_parameter('yellow_v_low', 150)
        self.declare_parameter('yellow_v_high', 220)
        self.declare_parameter('min_boundary_area', 180.0)
        self.declare_parameter('min_boundary_height_ratio', 0.25)
        self.declare_parameter('min_line_points', 25)
        self.declare_parameter('line_fit_max_residual_px', 12.0)
        self.declare_parameter('frame_timeout_sec', 0.5)
        self.declare_parameter('odom_timeout_sec', 0.5)
        self.declare_parameter('control_rate_hz', 20.0)
        self.declare_parameter('frame_log_interval_sec', 5.0)

        self._load_parameters()
        self._validate_parameters()
        self.state = DriveState.DISABLED
        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.last_frame_time = None
        self.last_odom_time = None
        self.current_x = None
        self.current_y = None
        self.current_yaw = None
        self.start_x = None
        self.start_y = None
        self.odom_distance = 0.0
        self.curve_start_x = None
        self.curve_start_y = None
        self.curve_start_yaw = None
        self.curve_target_x = None
        self.curve_target_y = None
        self.curve_target_yaw = None
        self.curve_points = None
        self.curve_yaws = None
        self.curve_curvatures = None
        self.curve_arc_lengths = None
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = None
        self.curve_position_error = None
        self.curve_yaw_error = None
        self.station_wait_started_at = None
        self.station_waypoint_x = None
        self.station_waypoint_y = None
        self.station_waypoint_yaw = None
        self.station_target_x = None
        self.station_target_y = None
        self.station_target_yaw = None
        self.test_forward_start_x = None
        self.test_forward_start_y = None
        self.test_forward_start_yaw = None
        self.test_forward_distance = 0.0
        self.test_forward_started_at = None
        self.waypoint_test_start_x = None
        self.waypoint_test_start_y = None
        self.waypoint_test_start_yaw = None
        self.waypoint_test_distance = 0.0
        self.waypoint_test_yaw_change = 0.0
        self.waypoint_test_started_at = None
        self.waypoint_motion_forward_distance = None
        self.waypoint_motion_rotate_angle = None
        self.waypoint_motion_rotate_max_angle = None
        self.waypoint_start_x = None
        self.waypoint_start_y = None
        self.waypoint_start_yaw = None
        self.station_final_approach_start_x = None
        self.station_final_approach_start_y = None
        self.station_final_approach_started_at = None
        self.station_final_approach_distance = 0.0
        self.station_final_approach_best_error = None
        self.station_final_previous_forward_to_target = None
        self.station_departure_requested = threading.Event()
        self.station_input_active = threading.Event()
        self.station_input_shutdown = threading.Event()
        self.harvest_goal_sent = False
        self.harvest_goal_accepted = False
        self.harvest_result_received = False
        self.harvest_success = False
        self.harvested_count = 0
        self.harvest_action_failed = False
        self.harvest_server_wait_logged = False
        self.harvest_goal_future = None
        self.harvest_result_future = None
        self.harvest_goal_handle = None
        self.harvest_shutting_down = False
        self.harvest_cycle_id = 0
        self.station_start_x = None
        self.station_start_y = None
        self.station_start_yaw = None
        self.next_stop_target_x = None
        self.next_stop_target_y = None
        self.next_stop_target_yaw = None
        self.next_stop_rotate_start_yaw = None
        self.next_stop_rotate_yaw_change = 0.0
        self.next_stop_rotate_started_at = None
        self.next_waypoint_wait_started_at = None
        self.next_waypoint_start_x = None
        self.next_waypoint_start_y = None
        self.next_waypoint_start_yaw = None
        self.next_waypoint_target_x = None
        self.next_waypoint_target_y = None
        self.next_waypoint_target_yaw = None
        self.final_camera_start_x = None
        self.final_camera_start_y = None
        self.final_camera_distance = 0.0
        self.final_straight_start_x = None
        self.final_straight_start_y = None
        self.final_straight_distance = 0.0
        self.final_straight_started_at = None
        self.last_linear_command = 0.0
        self.path_detected = False
        self.boundary_x = None
        self.target_x = int(round(self.target_x_config))
        self.path_error = None
        self.steering_command = 0.0
        self.frame_count = 0
        self.last_frame_log_time = self.get_clock().now()

        self.cmd_pub = self.create_publisher(
            Twist, str(self.get_parameter('cmd_vel_topic').value), 10)
        self.state_pub = self.create_publisher(
            String, '/camera_drive/state', 10)
        self.display_mode_pub = self.create_publisher(
            String, '/pinky/display_mode', 10)
        self.music_pub = self.create_publisher(
            String, '/pinky/music_control', 10)
        self.create_subscription(
            CompressedImage,
            str(self.get_parameter('camera_topic').value),
            self._image_callback,
            10,
        )
        self.create_subscription(
            Odometry,
            str(self.get_parameter('odom_topic').value),
            self._odom_callback,
            10,
        )
        self.create_service(
            SetBool, '/camera_drive/enable', self._enable_callback)
        self.timer = self.create_timer(
            1.0 / self.control_rate, self._control_tick)
        self.state_timer = self.create_timer(0.2, self._publish_drive_state)
        self.harvest_action_client = ActionClient(self, Harvest, '/harvest')
        self._publish_stop()
        self.get_logger().info(
            'ready but DISABLED; yellow boundary and odom are monitored only')
        self.station_input_thread = threading.Thread(
            target=self._station_input_worker,
            name='station_departure_input',
            daemon=False,
        )
        self.station_input_thread.start()

    def _load_parameters(self):
        self.linear_speed = float(self.get_parameter('linear_speed').value)
        self.max_linear_speed = float(
            self.get_parameter('max_linear_speed').value)
        self.max_angular_speed = float(
            self.get_parameter('max_angular_speed').value)
        self.kp = float(self.get_parameter('kp').value)
        self.steering_sign = float(
            self.get_parameter('steering_sign').value)
        self.target_distance_m = float(
            self.get_parameter('target_distance_m').value)
        self.curve_target_x_relative = float(
            self.get_parameter('curve_target_x_m').value)
        self.curve_target_y_relative = float(
            self.get_parameter('curve_target_y_m').value)
        self.curve_target_yaw_relative = math.radians(float(
            self.get_parameter('curve_target_yaw_deg').value))
        self.curve_position_tolerance = float(
            self.get_parameter('curve_position_tolerance_m').value)
        self.curve_yaw_tolerance = math.radians(float(
            self.get_parameter('curve_yaw_tolerance_deg').value))
        self.curve_linear_speed = float(
            self.get_parameter('curve_linear_speed').value)
        self.curve_min_linear_speed = float(
            self.get_parameter('curve_min_linear_speed').value)
        self.curve_kp_position = float(
            self.get_parameter('curve_kp_position').value)
        self.curve_kp_yaw = float(
            self.get_parameter('curve_kp_yaw').value)
        self.curve_start_handle = float(
            self.get_parameter('curve_start_handle_m').value)
        self.curve_end_handle = float(
            self.get_parameter('curve_end_handle_m').value)
        self.curve_lookahead = float(
            self.get_parameter('curve_lookahead_m').value)
        self.curve_sample_count = int(
            self.get_parameter('curve_sample_count').value)
        self.curve_timeout = float(
            self.get_parameter('curve_timeout_sec').value)
        self.curve_max_travel = float(
            self.get_parameter('curve_max_travel_m').value)
        self.station_stop_duration = float(
            self.get_parameter('station_stop_duration_sec').value)
        self.test_forward_mode = bool(
            self.get_parameter('test_forward_mode').value)
        self.test_forward_target = float(
            self.get_parameter('test_forward_distance_m').value)
        self.test_forward_speed = float(
            self.get_parameter('test_forward_speed').value)
        self.test_forward_timeout = float(
            self.get_parameter('test_forward_timeout_sec').value)
        self.test_forward_max_travel = float(
            self.get_parameter('test_forward_max_travel_m').value)
        self.station_target_forward = float(
            self.get_parameter('station_target_forward_m').value)
        self.station_target_right = float(
            self.get_parameter('station_target_right_m').value)
        self.station_target_yaw_relative = math.radians(float(
            self.get_parameter('station_target_yaw_deg').value))
        self.station_direct_mode = bool(
            self.get_parameter('station_direct_mode').value)
        self.waypoint_station_mode = bool(
            self.get_parameter('waypoint_station_mode').value)
        self.station_direct_start_handle = float(
            self.get_parameter('station_direct_start_handle_m').value)
        self.station_direct_end_handle = float(
            self.get_parameter('station_direct_end_handle_m').value)
        self.station_waypoint_forward = float(
            self.get_parameter('station_waypoint_forward_m').value)
        self.station_waypoint_right = float(
            self.get_parameter('station_waypoint_right_m').value)
        self.station_waypoint_yaw_relative = math.radians(float(
            self.get_parameter('station_waypoint_yaw_deg').value))
        self.station_waypoint_test_mode = bool(
            self.get_parameter('station_waypoint_test_mode').value)
        self.waypoint_forward_only_test_mode = bool(
            self.get_parameter('waypoint_forward_only_test_mode').value)
        self.waypoint_forward_rotate_test_mode = bool(
            self.get_parameter('waypoint_forward_rotate_test_mode').value)
        self.waypoint_forward_rotate_test_distance = float(
            self.get_parameter('waypoint_forward_rotate_test_distance_m').value)
        self.waypoint_forward_rotate_test_angle = math.radians(float(
            self.get_parameter('waypoint_forward_rotate_test_angle_deg').value))
        self.waypoint_forward_rotate_test_max_angle = math.radians(float(
            self.get_parameter('waypoint_forward_rotate_test_max_deg').value))
        self.waypoint_test_forward_distance = float(
            self.get_parameter('waypoint_test_forward_distance_m').value)
        self.waypoint_test_forward_speed = float(
            self.get_parameter('waypoint_test_forward_speed').value)
        self.waypoint_test_forward_timeout = float(
            self.get_parameter('waypoint_test_forward_timeout_sec').value)
        self.waypoint_test_forward_max_travel = float(
            self.get_parameter('waypoint_test_forward_max_travel_m').value)
        self.waypoint_test_rotate_angle = math.radians(float(
            self.get_parameter('waypoint_test_rotate_deg').value))
        self.waypoint_test_rotate_speed = float(
            self.get_parameter('waypoint_test_rotate_speed').value)
        self.waypoint_test_rotate_timeout = float(
            self.get_parameter('waypoint_test_rotate_timeout_sec').value)
        self.waypoint_test_rotate_max_angle = math.radians(float(
            self.get_parameter('waypoint_test_rotate_max_deg').value))
        self.waypoint_pose_settle_duration = float(
            self.get_parameter('waypoint_pose_settle_sec').value)
        self.station_waypoint_position_tolerance = float(
            self.get_parameter('station_waypoint_position_tolerance_m').value)
        self.station_waypoint_yaw_tolerance = math.radians(float(
            self.get_parameter('station_waypoint_yaw_tolerance_deg').value))
        self.station_waypoint_start_handle = float(
            self.get_parameter('station_waypoint_start_handle_m').value)
        self.station_waypoint_end_handle = float(
            self.get_parameter('station_waypoint_end_handle_m').value)
        self.station_waypoint_timeout = float(
            self.get_parameter('station_waypoint_timeout_sec').value)
        self.station_waypoint_max_travel = float(
            self.get_parameter('station_waypoint_max_travel_m').value)
        self.station_start_handle = float(
            self.get_parameter('station_start_handle_m').value)
        self.station_end_handle = float(
            self.get_parameter('station_end_handle_m').value)
        self.station_overshoot_tolerance = float(
            self.get_parameter('station_overshoot_tolerance_m').value)
        self.station_final_approach_max = float(
            self.get_parameter('station_final_approach_max_m').value)
        self.station_final_approach_enabled = bool(
            self.get_parameter('station_final_approach_enabled').value)
        self.station_final_approach_timeout = float(
            self.get_parameter('station_final_approach_timeout_sec').value)
        self.station_final_approach_speed = float(
            self.get_parameter('station_final_approach_speed').value)
        self.station_final_approach_max_angular = float(
            self.get_parameter('station_final_approach_max_angular').value)
        self.station_timeout = float(
            self.get_parameter('station_timeout_sec').value)
        self.station_max_travel = float(
            self.get_parameter('station_max_travel_m').value)
        self.manual_station_departure = bool(
            self.get_parameter('manual_station_departure').value)
        self.use_harvest_action = bool(
            self.get_parameter('use_harvest_action').value)
        self.harvest_target_count = int(
            self.get_parameter('harvest_target_count').value)
        self.next_stop_target_forward = float(
            self.get_parameter('next_stop_target_forward_m').value)
        self.next_stop_target_right = float(
            self.get_parameter('next_stop_target_right_m').value)
        self.next_stop_target_yaw_relative = math.radians(float(
            self.get_parameter('next_stop_target_yaw_deg').value))
        self.next_stop_start_handle = float(
            self.get_parameter('next_stop_start_handle_m').value)
        self.next_stop_end_handle = float(
            self.get_parameter('next_stop_end_handle_m').value)
        self.next_stop_max_angular_z = float(
            self.get_parameter('next_stop_max_angular_z').value)
        self.next_stop_max_angular_accel = float(
            self.get_parameter('next_stop_max_angular_accel').value)
        self.next_stop_final_rotate_angle = math.radians(float(
            self.get_parameter('next_stop_final_rotate_deg').value))
        self.next_stop_final_rotate_speed = float(
            self.get_parameter('next_stop_final_rotate_speed').value)
        self.next_stop_final_rotate_timeout = float(
            self.get_parameter('next_stop_final_rotate_timeout_sec').value)
        self.next_stop_final_rotate_max_angle = math.radians(float(
            self.get_parameter('next_stop_final_rotate_max_deg').value))
        self.next_waypoint_wait = float(
            self.get_parameter('next_waypoint_wait_sec').value)
        self.next_waypoint_target_forward = float(
            self.get_parameter('next_waypoint_target_forward_m').value)
        self.next_waypoint_target_right = float(
            self.get_parameter('next_waypoint_target_right_m').value)
        self.next_waypoint_target_yaw_relative = math.radians(float(
            self.get_parameter('next_waypoint_target_yaw_deg').value))
        self.next_waypoint_start_handle = float(
            self.get_parameter('next_waypoint_start_handle_m').value)
        self.next_waypoint_end_handle = float(
            self.get_parameter('next_waypoint_end_handle_m').value)
        self.final_camera_target_distance = float(
            self.get_parameter('final_camera_distance_m').value)
        self.final_straight_target_distance = float(
            self.get_parameter('final_straight_distance_m').value)
        self.final_straight_timeout = float(
            self.get_parameter('final_straight_timeout_sec').value)
        self.final_straight_max_travel = float(
            self.get_parameter('final_straight_max_travel_m').value)
        self.target_x_config = float(self.get_parameter('target_x').value)
        self.boundary_reference_x = float(
            self.get_parameter('boundary_reference_x').value)
        self.boundary_eval_y_ratio = float(
            self.get_parameter('boundary_eval_y_ratio').value)
        self.roi_top_ratio = float(
            self.get_parameter('roi_top_ratio').value)
        self.roi_left_ratio = float(
            self.get_parameter('roi_left_ratio').value)
        self.roi_right_ratio = float(
            self.get_parameter('roi_right_ratio').value)
        self.min_boundary_area = float(
            self.get_parameter('min_boundary_area').value)
        self.min_boundary_height_ratio = float(
            self.get_parameter('min_boundary_height_ratio').value)
        self.min_line_points = int(
            self.get_parameter('min_line_points').value)
        self.line_fit_max_residual = float(
            self.get_parameter('line_fit_max_residual_px').value)
        self.frame_timeout = float(
            self.get_parameter('frame_timeout_sec').value)
        self.odom_timeout = float(
            self.get_parameter('odom_timeout_sec').value)
        self.control_rate = float(
            self.get_parameter('control_rate_hz').value)

    def _validate_parameters(self):
        if not 0.0 < self.max_linear_speed <= 0.08:
            raise ValueError('max_linear_speed must be within (0.0, 0.08] m/s')
        if not 0.0 < self.linear_speed <= self.max_linear_speed:
            raise ValueError('linear_speed must not exceed max_linear_speed')
        if not 0.0 < self.max_angular_speed <= 0.15:
            raise ValueError('max_angular_speed must be within (0.0, 0.15]')
        if self.kp < 0.0 or self.steering_sign not in (-1.0, 1.0):
            raise ValueError('kp must be nonnegative and steering_sign +/-1')
        if self.target_distance_m <= 0.0:
            raise ValueError('target_distance_m must be positive')
        if self.harvest_target_count <= 0:
            raise ValueError('harvest_target_count must be positive')
        if not 0.0 < self.curve_linear_speed <= self.max_linear_speed:
            raise ValueError('curve_linear_speed exceeds max_linear_speed')
        if not 0.0 < self.curve_min_linear_speed <= self.curve_linear_speed:
            raise ValueError('invalid curve_min_linear_speed')
        if min(
                self.curve_position_tolerance,
                self.curve_yaw_tolerance,
                self.curve_start_handle,
                self.curve_end_handle,
                self.curve_lookahead,
                self.curve_timeout,
                self.curve_max_travel,
        ) <= 0.0:
            raise ValueError('curve tolerances/geometry/safety must be positive')
        if self.curve_sample_count < 20:
            raise ValueError('curve_sample_count must be at least 20')
        if min(
                self.station_stop_duration,
                self.station_direct_start_handle,
                self.station_direct_end_handle,
                self.test_forward_target,
                self.test_forward_speed,
                self.test_forward_timeout,
                self.test_forward_max_travel,
                self.station_waypoint_position_tolerance,
                self.station_waypoint_yaw_tolerance,
                self.station_waypoint_start_handle,
                self.station_waypoint_end_handle,
                self.station_waypoint_timeout,
                self.station_waypoint_max_travel,
                self.waypoint_test_forward_distance,
                self.waypoint_test_forward_speed,
                self.waypoint_test_forward_timeout,
                self.waypoint_test_forward_max_travel,
                self.waypoint_test_rotate_angle,
                self.waypoint_test_rotate_speed,
                self.waypoint_test_rotate_timeout,
                self.waypoint_test_rotate_max_angle,
                self.waypoint_forward_rotate_test_distance,
                self.waypoint_forward_rotate_test_angle,
                self.waypoint_forward_rotate_test_max_angle,
                self.station_start_handle,
                self.station_end_handle,
                self.station_overshoot_tolerance,
                self.station_final_approach_max,
                self.station_final_approach_timeout,
                self.station_final_approach_speed,
                self.station_final_approach_max_angular,
                self.station_timeout,
                self.station_max_travel,
                self.next_stop_start_handle,
                self.next_stop_end_handle,
                self.next_stop_max_angular_z,
                self.next_stop_max_angular_accel,
                self.next_stop_final_rotate_angle,
                self.next_stop_final_rotate_speed,
                self.next_stop_final_rotate_timeout,
                self.next_stop_final_rotate_max_angle,
                self.next_waypoint_wait,
                self.next_waypoint_start_handle,
                self.next_waypoint_end_handle,
                self.final_camera_target_distance,
                self.final_straight_target_distance,
                self.final_straight_timeout,
                self.final_straight_max_travel,
        ) <= 0.0:
            raise ValueError('station stop/safety parameters must be positive')
        if (self.final_straight_target_distance
                >= self.final_straight_max_travel):
            raise ValueError(
                'final straight target must be below its travel safety limit')
        if self.test_forward_speed > self.max_linear_speed:
            raise ValueError('test_forward_speed exceeds max_linear_speed')
        if self.test_forward_target >= self.test_forward_max_travel:
            raise ValueError(
                'test forward target must be below its travel safety limit')
        if self.waypoint_test_forward_speed > self.max_linear_speed:
            raise ValueError('waypoint test forward speed exceeds safety limit')
        if (self.waypoint_test_forward_distance
                >= self.waypoint_test_forward_max_travel):
            raise ValueError('waypoint test forward target exceeds travel limit')
        if self.waypoint_test_rotate_speed > self.max_angular_speed:
            raise ValueError('waypoint test rotate speed exceeds safety limit')
        if self.waypoint_test_rotate_angle >= self.waypoint_test_rotate_max_angle:
            raise ValueError('waypoint test rotate target exceeds angle limit')
        if (self.waypoint_forward_rotate_test_distance
                >= self.waypoint_test_forward_max_travel):
            raise ValueError('forward-rotate test target exceeds travel limit')
        if (self.waypoint_forward_rotate_test_angle
                >= self.waypoint_forward_rotate_test_max_angle):
            raise ValueError('forward-rotate test target exceeds angle limit')
        if self.station_final_approach_speed > self.max_linear_speed:
            raise ValueError(
                'station_final_approach_speed exceeds max_linear_speed')
        if self.station_final_approach_max_angular > self.max_angular_speed:
            raise ValueError(
                'station_final_approach_max_angular exceeds max_angular_speed')
        if self.next_stop_max_angular_z > self.max_angular_speed:
            raise ValueError(
                'next_stop_max_angular_z exceeds max_angular_speed')
        if self.next_stop_final_rotate_speed > self.max_angular_speed:
            raise ValueError(
                'next_stop_final_rotate_speed exceeds max_angular_speed')
        if (self.next_stop_final_rotate_angle
                >= self.next_stop_final_rotate_max_angle):
            raise ValueError(
                'next stop final rotate target exceeds angle limit')
        if math.hypot(
                self.station_target_forward,
                self.station_target_right,
        ) <= 0.0:
            raise ValueError('station target displacement must be nonzero')
        if math.hypot(
                self.station_waypoint_forward,
                self.station_waypoint_right,
        ) <= 0.0:
            raise ValueError('station waypoint displacement must be nonzero')
        if self.station_target_forward < 0.0 or self.station_target_right < 0.0:
            raise ValueError('station forward/right distances must be nonnegative')
        if (self.next_stop_target_forward < 0.0
                or self.next_stop_target_right < 0.0):
            raise ValueError('next stop forward/right distances must be nonnegative')
        if math.hypot(
                self.next_stop_target_forward,
                self.next_stop_target_right,
        ) <= 0.0:
            raise ValueError('next stop target displacement must be nonzero')
        if (self.next_waypoint_target_forward < 0.0
                or self.next_waypoint_target_right < 0.0):
            raise ValueError(
                'next waypoint forward/right distances must be nonnegative')
        if math.hypot(
                self.next_waypoint_target_forward,
                self.next_waypoint_target_right,
        ) <= 0.0:
            raise ValueError('next waypoint target displacement must be nonzero')
        if (self.station_waypoint_forward < 0.0
                or self.station_waypoint_right < 0.0):
            raise ValueError('waypoint forward/right distances must be nonnegative')
        if self.target_x_config < 0.0 or self.boundary_reference_x < 0.0:
            raise ValueError('target and boundary reference x must be nonnegative')
        if not (0.0 <= self.roi_left_ratio < self.roi_right_ratio <= 1.0):
            raise ValueError('x ROI ratios must satisfy 0 <= left < right <= 1')
        if not 0.0 <= self.roi_top_ratio < 1.0:
            raise ValueError('roi_top_ratio must be within [0, 1)')
        if not self.roi_top_ratio <= self.boundary_eval_y_ratio < 1.0:
            raise ValueError('boundary_eval_y_ratio must be inside the ROI')
        if not 0.0 < self.min_boundary_height_ratio <= 1.0:
            raise ValueError('min_boundary_height_ratio must be within (0, 1]')
        if self.min_line_points < 2 or self.line_fit_max_residual <= 0.0:
            raise ValueError('line fit point count/residual must be positive')
        if min(self.frame_timeout, self.odom_timeout, self.control_rate) <= 0.0:
            raise ValueError('timeouts and control rate must be positive')
        hsv_values = [
            int(self.get_parameter(name).value)
            for name in (
                'yellow_h_low', 'yellow_h_high',
                'yellow_s_low', 'yellow_s_high',
                'yellow_v_low', 'yellow_v_high',
            )
        ]
        if not all(0 <= value <= 255 for value in hsv_values):
            raise ValueError('HSV parameters must be within [0, 255]')

    def _image_callback(self, msg: CompressedImage):
        encoded = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            if self.state in (
                    DriveState.CAMERA_DRIVING,
                    DriveState.FINAL_CAMERA_DRIVING):
                self._enter_fault('compressed camera frame decode failed')
            return
        self.last_frame_time = self.get_clock().now()
        self.frame_count += 1
        if self.state in (
                DriveState.DISABLED,
                DriveState.CAMERA_DRIVING,
                DriveState.FINAL_CAMERA_DRIVING):
            self._detect_yellow_boundary(frame)
        self._log_status_if_due()

    def _detect_yellow_boundary(self, frame):
        height, width = frame.shape[:2]
        top = int(height * self.roi_top_ratio)
        left = int(width * self.roi_left_ratio)
        right = int(width * self.roi_right_ratio)
        roi = frame[top:height, left:right]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower = np.array([
            int(self.get_parameter('yellow_h_low').value),
            int(self.get_parameter('yellow_s_low').value),
            int(self.get_parameter('yellow_v_low').value),
        ], dtype=np.uint8)
        upper = np.array([
            int(self.get_parameter('yellow_h_high').value),
            int(self.get_parameter('yellow_s_high').value),
            int(self.get_parameter('yellow_v_high').value),
        ], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_height = roi.shape[0] * self.min_boundary_height_ratio
        candidates = []
        for contour in contours:
            x, y, box_width, box_height = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area >= self.min_boundary_area and box_height >= min_height:
                # Height is weighted strongly so a long boundary is preferred
                # over a compact yellow object with a similar area.
                score = box_height * 10.0 + area / max(box_width, 1)
                candidates.append((score, contour))
        if not candidates:
            self._clear_detection()
            if self.state in (
                    DriveState.CAMERA_DRIVING,
                    DriveState.FINAL_CAMERA_DRIVING):
                self._enter_fault('yellow boundary detection lost')
            return

        contour = max(candidates, key=lambda item: item[0])[1]
        contour_mask = np.zeros_like(mask)
        cv2.drawContours(contour_mask, [contour], -1, 255, thickness=-1)

        # Use the road-facing (rightmost) yellow edge from every image row.
        # This gives many points for x=f(y), rather than one contour center.
        edge_y = []
        edge_x = []
        for local_y in range(contour_mask.shape[0]):
            columns = np.flatnonzero(contour_mask[local_y])
            if columns.size:
                edge_y.append(float(top + local_y))
                edge_x.append(float(left + columns.max()))
        if len(edge_x) < self.min_line_points:
            self._clear_detection()
            if self.state in (
                    DriveState.CAMERA_DRIVING,
                    DriveState.FINAL_CAMERA_DRIVING):
                self._enter_fault('not enough yellow edge points for line fit')
            return

        edge_y = np.asarray(edge_y)
        edge_x = np.asarray(edge_x)
        slope, intercept = np.polyfit(edge_y, edge_x, 1)
        residual = np.abs(edge_x - (slope * edge_y + intercept))
        inliers = residual <= self.line_fit_max_residual
        if int(np.count_nonzero(inliers)) < self.min_line_points:
            self._clear_detection()
            if self.state in (
                    DriveState.CAMERA_DRIVING,
                    DriveState.FINAL_CAMERA_DRIVING):
                self._enter_fault('yellow boundary line fit rejected')
            return
        slope, intercept = np.polyfit(edge_y[inliers], edge_x[inliers], 1)
        evaluation_y = height * self.boundary_eval_y_ratio
        boundary_x = slope * evaluation_y + intercept

        # In the centered calibration image, boundary_reference_x corresponds
        # to a desired path at target_x. Boundary movement shifts that
        # estimated path by the same number of pixels; no metric conversion.
        estimated_path_x = (
            self.target_x_config
            + (boundary_x - self.boundary_reference_x)
        )
        error = estimated_path_x - self.target_x_config
        angular = self.steering_sign * self.kp * error
        angular = max(
            -self.max_angular_speed,
            min(self.max_angular_speed, angular),
        )
        self.path_detected = True
        self.boundary_x = int(round(boundary_x))
        self.target_x = int(round(self.target_x_config))
        self.path_error = int(round(error))
        self.steering_command = angular

    def _clear_detection(self):
        self.path_detected = False
        self.boundary_x = None
        self.target_x = int(round(self.target_x_config))
        self.path_error = None
        self.steering_command = 0.0

    def _odom_callback(self, msg: Odometry):
        self.last_odom_time = self.get_clock().now()
        self.current_x = float(msg.pose.pose.position.x)
        self.current_y = float(msg.pose.pose.position.y)
        q = msg.pose.pose.orientation
        self.current_yaw = self._yaw_from_quaternion(q.x, q.y, q.z, q.w)
        if self.state in (
                DriveState.CURVE_TO_FIRST_POINT,
                DriveState.STATION_TO_WAYPOINT,
                DriveState.STATION_MOVE,
                DriveState.STATION_MOVE_FROM_WAYPOINT,
                DriveState.NEXT_WAYPOINT_MOVE,
        ):
            self.curve_distance = math.hypot(
                self.current_x - self.curve_start_x,
                self.current_y - self.curve_start_y,
            )
            return
        if self.state == DriveState.STATION_FINAL_APPROACH:
            self.station_final_approach_distance = math.hypot(
                self.current_x - self.station_final_approach_start_x,
                self.current_y - self.station_final_approach_start_y,
            )
            return
        if self.state == DriveState.TEST_FORWARD_MOVE:
            self.test_forward_distance = math.hypot(
                self.current_x - self.test_forward_start_x,
                self.current_y - self.test_forward_start_y,
            )
            if self.test_forward_distance >= self.test_forward_max_travel:
                self._enter_fault('test forward travel safety limit exceeded')
                return
            if self.test_forward_distance >= self.test_forward_target:
                self._finish_test_forward()
            return
        if self.state == DriveState.WAYPOINT_TEST_FORWARD:
            self.waypoint_test_distance = math.hypot(
                self.current_x - self.waypoint_test_start_x,
                self.current_y - self.waypoint_test_start_y,
            )
            if (self.waypoint_test_distance
                    >= self.waypoint_test_forward_max_travel):
                self._enter_fault(
                    'waypoint test forward travel safety limit exceeded')
                return
            if (self.waypoint_test_distance
                    >= self.waypoint_motion_forward_distance):
                self._finish_waypoint_test_forward()
            return
        if self.state == DriveState.WAYPOINT_TEST_ROTATE:
            self.waypoint_test_yaw_change = self._normalize_angle(
                self.current_yaw - self.waypoint_test_start_yaw)
            if abs(self.waypoint_test_yaw_change) >= (
                    self.waypoint_motion_rotate_max_angle):
                self._enter_fault(
                    'waypoint test rotation safety limit exceeded')
                return
            if self.waypoint_test_yaw_change <= -self.waypoint_motion_rotate_angle:
                self._finish_waypoint_test_rotate()
            return
        if self.state == DriveState.NEXT_STOP_FINAL_ROTATE:
            self.next_stop_rotate_yaw_change = self._normalize_angle(
                self.current_yaw - self.next_stop_rotate_start_yaw)
            if abs(self.next_stop_rotate_yaw_change) >= (
                    self.next_stop_final_rotate_max_angle):
                self._enter_fault(
                    'next stop final rotation safety limit exceeded')
                return
            if (self.next_stop_rotate_yaw_change
                    <= -self.next_stop_final_rotate_angle):
                self._finish_next_stop_final_rotate()
            return
        if self.state == DriveState.FINAL_CAMERA_DRIVING:
            self.final_camera_distance = math.hypot(
                self.current_x - self.final_camera_start_x,
                self.current_y - self.final_camera_start_y,
            )
            if self.final_camera_distance >= self.final_camera_target_distance:
                self._start_final_straight_drive()
            return
        if self.state == DriveState.FINAL_STRAIGHT_DRIVING:
            self.final_straight_distance = math.hypot(
                self.current_x - self.final_straight_start_x,
                self.current_y - self.final_straight_start_y,
            )
            if self.final_straight_distance >= self.final_straight_max_travel:
                self._enter_fault('final straight travel safety limit exceeded')
                return
            if (self.final_straight_distance
                    >= self.final_straight_target_distance):
                self._finish_final_drive()
            return
        if self.state != DriveState.CAMERA_DRIVING:
            return
        self.odom_distance = math.hypot(
            self.current_x - self.start_x,
            self.current_y - self.start_y,
        )
        if self.odom_distance >= self.target_distance_m:
            self.command_active = False
            self.state = DriveState.TARGET_81CM_REACHED
            self._publish_stop(repeat=3)
            self.get_logger().warning(
                f'TARGET 0.81M REACHED: {self.odom_distance:.3f} m; '
                'starting smooth curve')
            self._start_curve()

    def _control_tick(self):
        sequence_state = self.state in (
            DriveState.FIRST_POINT_REACHED,
            DriveState.STATION_WAIT,
            DriveState.TEST_FORWARD_MOVE,
            DriveState.WAYPOINT_TEST_FORWARD,
            DriveState.WAYPOINT_TEST_ROTATE,
            DriveState.WAYPOINT_SETTLE,
            DriveState.WAYPOINT_REACHED,
            DriveState.STATION_TO_WAYPOINT,
            DriveState.STATION_WAYPOINT_REACHED,
            DriveState.STATION_MOVE,
            DriveState.STATION_MOVE_FROM_WAYPOINT,
            DriveState.STATION_FINAL_APPROACH,
            DriveState.STATION_LOAD_WAIT,
            DriveState.STATION_TO_NEXT_STOP,
            DriveState.NEXT_STOP_FINAL_ROTATE,
            DriveState.NEXT_WAYPOINT_WAIT,
            DriveState.NEXT_WAYPOINT_MOVE,
            DriveState.FINAL_CAMERA_DRIVING,
            DriveState.FINAL_STRAIGHT_DRIVING,
        )
        if not self.enabled and not (self.sequence_active and sequence_state):
            return
        now = self.get_clock().now()
        if self._is_stale(now, self.last_odom_time, self.odom_timeout):
            self._enter_fault('odom timeout')
            return
        if self.state == DriveState.CAMERA_DRIVING:
            self._control_camera_drive(now)
        elif self.state == DriveState.CURVE_TO_FIRST_POINT:
            self._control_curve(now)
        elif self.state == DriveState.FIRST_POINT_REACHED:
            self._start_station_wait()
        elif self.state == DriveState.STATION_WAIT:
            self._control_station_wait(now)
        elif self.state == DriveState.TEST_FORWARD_MOVE:
            self._control_test_forward(now)
        elif self.state == DriveState.WAYPOINT_TEST_FORWARD:
            self._control_waypoint_test_forward(now)
        elif self.state == DriveState.WAYPOINT_TEST_ROTATE:
            self._control_waypoint_test_rotate(now)
        elif self.state == DriveState.WAYPOINT_SETTLE:
            self._control_waypoint_settle(now)
        elif self.state == DriveState.STATION_TO_WAYPOINT:
            self._control_curve(now)
        elif self.state == DriveState.STATION_MOVE:
            self._control_curve(now)
        elif self.state == DriveState.STATION_MOVE_FROM_WAYPOINT:
            self._control_curve(now)
        elif self.state == DriveState.STATION_FINAL_APPROACH:
            self._control_station_final_approach(now)
        elif self.state == DriveState.STATION_LOAD_WAIT:
            self._control_station_load_wait(now)
        elif self.state == DriveState.STATION_TO_NEXT_STOP:
            self._control_curve(now)
        elif self.state == DriveState.NEXT_STOP_FINAL_ROTATE:
            self._control_next_stop_final_rotate(now)
        elif self.state == DriveState.NEXT_WAYPOINT_WAIT:
            self._control_next_waypoint_wait(now)
        elif self.state == DriveState.NEXT_WAYPOINT_MOVE:
            self._control_curve(now)
        elif self.state == DriveState.FINAL_CAMERA_DRIVING:
            self._control_camera_drive(now)
        elif self.state == DriveState.FINAL_STRAIGHT_DRIVING:
            self._control_final_straight_drive(now)

    def _control_camera_drive(self, now):
        if self._is_stale(now, self.last_frame_time, self.frame_timeout):
            self._enter_fault('camera frame timeout')
            return
        if not self.path_detected:
            if self.state == DriveState.FINAL_CAMERA_DRIVING:
                self._publish_stop()
                return
            self._enter_fault('yellow boundary unavailable')
            return

        command = Twist()
        command.linear.x = min(self.linear_speed, self.max_linear_speed)
        command.angular.z = self.steering_command
        self.cmd_pub.publish(command)
        self.last_linear_command = command.linear.x
        if not self.command_active:
            self.get_logger().info(
                f'CAMERA_DRIVING: linear.x={command.linear.x:.3f}, '
                f'angular.z={command.angular.z:.3f}')
        self.command_active = True

    def _start_curve(self):
        self.curve_start_x = self.current_x
        self.curve_start_y = self.current_y
        self.curve_start_yaw = self.current_yaw
        cosine = math.cos(self.curve_start_yaw)
        sine = math.sin(self.curve_start_yaw)
        self.curve_target_x = (
            self.curve_start_x
            + cosine * self.curve_target_x_relative
            - sine * self.curve_target_y_relative
        )
        self.curve_target_y = (
            self.curve_start_y
            + sine * self.curve_target_x_relative
            + cosine * self.curve_target_y_relative
        )
        self.curve_target_yaw = self._normalize_angle(
            self.curve_start_yaw + self.curve_target_yaw_relative)
        self._build_bezier_trajectory()
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = self.get_clock().now()
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.CURVE_TO_FIRST_POINT
        self.get_logger().warning(
            'CURVE_TO_FIRST_POINT: '
            f'target=({self.curve_target_x:.3f}, '
            f'{self.curve_target_y:.3f}, '
            f'{math.degrees(self.curve_target_yaw):.1f}deg)')

    def _build_bezier_trajectory(self, start_handle=None, end_handle=None):
        if start_handle is None:
            start_handle = self.curve_start_handle
        if end_handle is None:
            end_handle = self.curve_end_handle
        p0 = np.array([self.curve_start_x, self.curve_start_y])
        p3 = np.array([self.curve_target_x, self.curve_target_y])
        p1 = p0 + start_handle * np.array([
            math.cos(self.curve_start_yaw),
            math.sin(self.curve_start_yaw),
        ])
        p2 = p3 - end_handle * np.array([
            math.cos(self.curve_target_yaw),
            math.sin(self.curve_target_yaw),
        ])
        t = np.linspace(0.0, 1.0, self.curve_sample_count)
        one_minus_t = 1.0 - t
        points = (
            one_minus_t[:, None] ** 3 * p0
            + 3.0 * one_minus_t[:, None] ** 2 * t[:, None] * p1
            + 3.0 * one_minus_t[:, None] * t[:, None] ** 2 * p2
            + t[:, None] ** 3 * p3
        )
        derivative = (
            3.0 * one_minus_t[:, None] ** 2 * (p1 - p0)
            + 6.0 * one_minus_t[:, None] * t[:, None] * (p2 - p1)
            + 3.0 * t[:, None] ** 2 * (p3 - p2)
        )
        second_derivative = (
            6.0 * one_minus_t[:, None] * (p2 - 2.0 * p1 + p0)
            + 6.0 * t[:, None] * (p3 - 2.0 * p2 + p1)
        )
        speed_squared = np.sum(derivative ** 2, axis=1)
        denominator = np.maximum(speed_squared ** 1.5, 1e-9)
        curvature = (
            derivative[:, 0] * second_derivative[:, 1]
            - derivative[:, 1] * second_derivative[:, 0]
        ) / denominator
        segment_lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
        self.curve_points = points
        self.curve_yaws = np.arctan2(derivative[:, 1], derivative[:, 0])
        self.curve_curvatures = curvature
        self.curve_arc_lengths = np.concatenate((
            np.array([0.0]), np.cumsum(segment_lengths)))

    @staticmethod
    def _sample_bezier_segment(
            p0, p3, start_yaw, end_yaw, start_handle, end_handle,
            sample_count):
        p1 = p0 + start_handle * np.array([
            math.cos(start_yaw), math.sin(start_yaw)])
        p2 = p3 - end_handle * np.array([
            math.cos(end_yaw), math.sin(end_yaw)])
        t = np.linspace(0.0, 1.0, sample_count)
        one_minus_t = 1.0 - t
        points = (
            one_minus_t[:, None] ** 3 * p0
            + 3.0 * one_minus_t[:, None] ** 2 * t[:, None] * p1
            + 3.0 * one_minus_t[:, None] * t[:, None] ** 2 * p2
            + t[:, None] ** 3 * p3
        )
        derivative = (
            3.0 * one_minus_t[:, None] ** 2 * (p1 - p0)
            + 6.0 * one_minus_t[:, None] * t[:, None] * (p2 - p1)
            + 3.0 * t[:, None] ** 2 * (p3 - p2)
        )
        second_derivative = (
            6.0 * one_minus_t[:, None] * (p2 - 2.0 * p1 + p0)
            + 6.0 * t[:, None] * (p3 - 2.0 * p2 + p1)
        )
        speed_squared = np.sum(derivative ** 2, axis=1)
        denominator = np.maximum(speed_squared ** 1.5, 1e-9)
        curvature = (
            derivative[:, 0] * second_derivative[:, 1]
            - derivative[:, 1] * second_derivative[:, 0]
        ) / denominator
        yaws = np.arctan2(derivative[:, 1], derivative[:, 0])
        return points, yaws, curvature

    def _control_curve(self, now):
        elapsed = (now - self.curve_started_at).nanoseconds / 1e9
        station_move = self.state in (
            DriveState.STATION_MOVE,
            DriveState.STATION_MOVE_FROM_WAYPOINT,
            DriveState.STATION_TO_NEXT_STOP,
            DriveState.NEXT_WAYPOINT_MOVE,
        )
        waypoint_move = self.state == DriveState.STATION_TO_WAYPOINT
        if station_move:
            timeout = self.station_timeout
            max_travel = self.station_max_travel
            motion_name = 'station move'
        elif waypoint_move:
            timeout = self.station_waypoint_timeout
            max_travel = self.station_waypoint_max_travel
            motion_name = 'station waypoint'
        else:
            timeout = self.curve_timeout
            max_travel = self.curve_max_travel
            motion_name = 'curve'
        if elapsed >= timeout:
            self._enter_fault(f'{motion_name} timeout')
            return
        if self.curve_distance >= max_travel:
            self._enter_fault(f'{motion_name} travel safety limit exceeded')
            return

        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        position_tolerance = (
            self.station_waypoint_position_tolerance
            if waypoint_move else self.curve_position_tolerance)
        yaw_tolerance = (
            self.station_waypoint_yaw_tolerance
            if waypoint_move else self.curve_yaw_tolerance)
        if (
                self.curve_position_error <= position_tolerance
                and abs(self.curve_yaw_error) <= yaw_tolerance
        ):
            if station_move:
                if self.state == DriveState.STATION_TO_NEXT_STOP:
                    self._finish_next_stop()
                elif self.state == DriveState.NEXT_WAYPOINT_MOVE:
                    self._finish_next_waypoint()
                else:
                    self._finish_station()
                return
            if waypoint_move:
                self._finish_station_waypoint(now)
                return
            self.command_active = False
            self.last_linear_command = 0.0
            self.steering_command = 0.0
            self._publish_stop(repeat=5)
            self.enabled = False
            self._prepare_station_target(now)
            return

        current = np.array([self.current_x, self.current_y])
        remaining_points = self.curve_points[self.curve_progress_index:]
        nearest_offset = int(np.argmin(
            np.linalg.norm(remaining_points - current, axis=1)))
        self.curve_progress_index += nearest_offset
        remaining_path = max(
            0.0,
            self.curve_arc_lengths[-1]
            - self.curve_arc_lengths[self.curve_progress_index],
        )
        if station_move or waypoint_move:
            terminal_dx = self.current_x - self.curve_target_x
            terminal_dy = self.current_y - self.curve_target_y
            distance_past_target = (
                math.cos(self.curve_target_yaw) * terminal_dx
                + math.sin(self.curve_target_yaw) * terminal_dy
            )
            if distance_past_target > self.station_overshoot_tolerance:
                self._enter_fault(f'{motion_name} target overshoot detected')
                return
            if self.curve_progress_index >= len(self.curve_points) - 1:
                if station_move:
                    if self.state == DriveState.STATION_TO_NEXT_STOP:
                        self._finish_next_stop(path_complete=True)
                    elif self.state == DriveState.NEXT_WAYPOINT_MOVE:
                        self._finish_next_waypoint(path_complete=True)
                    elif self.station_final_approach_enabled:
                        self._start_station_final_approach(now)
                    else:
                        self._finish_station(path_complete=True)
                else:
                    self._enter_fault(
                        'station waypoint path exhausted before pose tolerance')
                return
        desired_arc = (
            self.curve_arc_lengths[self.curve_progress_index]
            + self.curve_lookahead
        )
        reference_index = int(np.searchsorted(
            self.curve_arc_lengths, desired_arc, side='left'))
        reference_index = min(reference_index, len(self.curve_points) - 1)
        reference = self.curve_points[reference_index]
        reference_yaw = float(self.curve_yaws[reference_index])
        curvature = float(self.curve_curvatures[reference_index])

        dx = self.current_x - reference[0]
        dy = self.current_y - reference[1]
        cross_track_error = (
            -math.sin(reference_yaw) * dx
            + math.cos(reference_yaw) * dy
        )
        heading_error = self._normalize_angle(
            reference_yaw - self.current_yaw)
        speed_from_goal = max(
            self.curve_min_linear_speed,
            min(self.curve_linear_speed, self.curve_position_error * 0.8),
        )
        if station_move or waypoint_move:
            speed_from_remaining_path = max(
                self.curve_min_linear_speed,
                remaining_path * 0.8,
            )
            speed_from_goal = min(
                speed_from_goal, speed_from_remaining_path)
        if abs(curvature) > 1e-6:
            speed_from_curvature = self.max_angular_speed / abs(curvature)
            linear = max(
                self.curve_min_linear_speed,
                min(speed_from_goal, speed_from_curvature),
            )
        else:
            linear = speed_from_goal
        angular = (
            linear * curvature
            - self.curve_kp_position * cross_track_error
            + self.curve_kp_yaw * heading_error
        )
        angular = max(
            -self.max_angular_speed,
            min(self.max_angular_speed, angular),
        )
        if self.state == DriveState.STATION_TO_NEXT_STOP:
            angular = max(
                -self.next_stop_max_angular_z,
                min(self.next_stop_max_angular_z, angular),
            )
            max_angular_step = (
                self.next_stop_max_angular_accel / self.control_rate)
            angular = max(
                self.steering_command - max_angular_step,
                min(self.steering_command + max_angular_step, angular),
            )
        command = Twist()
        command.linear.x = min(linear, self.max_linear_speed)
        command.angular.z = angular
        self.cmd_pub.publish(command)
        self.last_linear_command = command.linear.x
        self.steering_command = command.angular.z
        self.command_active = True

    def _station_pose_reached(self):
        return (
            self.curve_position_error <= self.curve_position_tolerance
            and abs(self.curve_yaw_error) <= self.curve_yaw_tolerance
        )

    def _finish_station(self, path_complete=False):
        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.state = DriveState.STATION_REACHED
        self._publish_stop(repeat=5)
        if path_complete:
            message = 'STATION_REACHED: Bezier path complete; STOPPING'
        else:
            message = 'STATION_REACHED: target pose tolerance satisfied; STOPPING'
        self.get_logger().warning(message)
        if self.use_harvest_action or self.manual_station_departure:
            self.sequence_active = True
            self._start_station_load_wait()

    def _start_station_load_wait(self):
        self.state = DriveState.STATION_LOAD_WAIT
        self.station_departure_requested.clear()
        self._reset_harvest_action_state()
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop(repeat=5)
        if self.use_harvest_action:
            prompt = (
                'STATION 정지 완료; /harvest Action Server를 기다립니다.')
            self.station_input_active.clear()
        else:
            prompt = 'STATION 상차 완료 후 ENTER를 누르면 다음 STOP으로 출발합니다.'
            self.station_input_active.set()
        self.get_logger().warning(prompt)
        print(prompt, flush=True)

    def _reset_harvest_action_state(self):
        self.harvest_cycle_id += 1
        self.harvest_goal_sent = False
        self.harvest_goal_accepted = False
        self.harvest_result_received = False
        self.harvest_success = False
        self.harvested_count = 0
        self.harvest_action_failed = False
        self.harvest_server_wait_logged = False
        self.harvest_goal_future = None
        self.harvest_result_future = None
        self.harvest_goal_handle = None

    def _send_harvest_goal(self):
        if self.harvest_goal_sent or self.harvest_action_failed:
            return
        self.harvest_goal_sent = True
        goal = Harvest.Goal()
        goal.target_count = self.harvest_target_count
        self.get_logger().warning(
            f'Sending Harvest goal: target_count={goal.target_count}')
        try:
            cycle_id = self.harvest_cycle_id
            self.harvest_goal_future = self.harvest_action_client.send_goal_async(
                goal, feedback_callback=self._harvest_feedback_callback)
            self.harvest_goal_future.add_done_callback(
                lambda future: self._harvest_goal_response_callback(
                    future, cycle_id))
        except Exception as error:
            self.harvest_action_failed = True
            self.get_logger().error(
                f'Harvest goal send failed; remaining stopped: {error}')

    def _harvest_goal_response_callback(self, future, cycle_id):
        if (self.harvest_shutting_down
                or cycle_id != self.harvest_cycle_id):
            return
        try:
            goal_handle = future.result()
        except Exception as error:
            self.harvest_action_failed = True
            self.get_logger().error(
                f'Harvest goal response failed; remaining stopped: {error}')
            return
        if not goal_handle.accepted:
            self.harvest_action_failed = True
            self.get_logger().error(
                'Harvest goal rejected; remaining stopped at STATION')
            return
        self.harvest_goal_accepted = True
        self.harvest_goal_handle = goal_handle
        self.get_logger().warning('Harvest goal accepted; waiting for result')
        self.harvest_result_future = goal_handle.get_result_async()
        self.harvest_result_future.add_done_callback(
            lambda future: self._harvest_result_callback(future, cycle_id))

    def _harvest_feedback_callback(self, feedback_message):
        if self.harvest_shutting_down:
            return
        feedback = feedback_message.feedback
        self.get_logger().info(
            'Harvest feedback: '
            f'current_count={feedback.current_count}, status={feedback.status}')

    def _harvest_result_callback(self, future, cycle_id):
        if (self.harvest_shutting_down
                or cycle_id != self.harvest_cycle_id):
            return
        try:
            result = future.result().result
        except Exception as error:
            self.harvest_action_failed = True
            self.get_logger().error(
                f'Harvest result failed; remaining stopped: {error}')
            return
        self.harvested_count = int(result.harvested_count)
        self.harvest_success = bool(
            result.success
            and self.harvested_count >= self.harvest_target_count)
        self.harvest_result_received = True
        if self.harvest_success:
            self.get_logger().warning(
                'Harvest succeeded: '
                f'harvested_count={self.harvested_count}')
        else:
            self.harvest_action_failed = True
            self.get_logger().error(
                'Harvest result did not satisfy departure condition: '
                f'success={result.success}, '
                f'harvested_count={self.harvested_count}, '
                f'target_count={self.harvest_target_count}; remaining stopped')

    def _station_input_worker(self):
        input_stream = None
        owns_stream = False
        try:
            try:
                input_stream = open('/dev/tty', 'r', encoding='utf-8')
                owns_stream = True
            except OSError:
                input_stream = sys.stdin

            while not self.station_input_shutdown.is_set():
                if not self.station_input_active.wait(timeout=0.1):
                    continue
                if self.station_input_shutdown.is_set():
                    break
                try:
                    readable, _, _ = select.select(
                        [input_stream], [], [], 0.1)
                except (OSError, ValueError):
                    self.get_logger().error(
                        'terminal input unavailable; remaining stopped in '
                        'STATION_LOAD_WAIT')
                    self.station_input_active.clear()
                    continue
                if not readable:
                    continue
                try:
                    line = input_stream.readline()
                except (EOFError, KeyboardInterrupt, OSError):
                    self.get_logger().warning(
                        'station departure input cancelled safely')
                    self.station_input_active.clear()
                    continue
                if line == '':
                    self.get_logger().error(
                        'terminal input reached EOF; remaining stopped in '
                        'STATION_LOAD_WAIT')
                    self.station_input_active.clear()
                    continue
                self.station_departure_requested.set()
                self.station_input_active.clear()
                self.get_logger().warning(
                    'ENTER detected: preparing STATION departure')
        finally:
            if owns_stream and input_stream is not None:
                input_stream.close()

    def _control_station_load_wait(self, now):
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop()
        if self.use_harvest_action:
            if self.harvest_action_failed:
                return
            if not self.harvest_goal_sent:
                if not self.harvest_action_client.server_is_ready():
                    if not self.harvest_server_wait_logged:
                        self.get_logger().warning(
                            '/harvest server unavailable; remaining stopped')
                        self.harvest_server_wait_logged = True
                    return
                self._send_harvest_goal()
                return
            if not self.harvest_result_received:
                return
            if not self.harvest_success:
                return
            self.harvest_result_received = False
            self._start_next_stop_from_station(now)
            return
        if not self.station_departure_requested.is_set():
            return
        self.station_departure_requested.clear()
        self.station_input_active.clear()
        self._start_next_stop_from_station(now)

    def _start_next_stop_from_station(self, now):
        self.station_start_x = self.current_x
        self.station_start_y = self.current_y
        self.station_start_yaw = self.current_yaw
        cosine = math.cos(self.station_start_yaw)
        sine = math.sin(self.station_start_yaw)
        local_y = -self.next_stop_target_right
        self.next_stop_target_x = (
            self.station_start_x
            + cosine * self.next_stop_target_forward
            - sine * local_y
        )
        self.next_stop_target_y = (
            self.station_start_y
            + sine * self.next_stop_target_forward
            + cosine * local_y
        )
        self.next_stop_target_yaw = self._normalize_angle(
            self.station_start_yaw + self.next_stop_target_yaw_relative)
        self.curve_start_x = self.station_start_x
        self.curve_start_y = self.station_start_y
        self.curve_start_yaw = self.station_start_yaw
        self.curve_target_x = self.next_stop_target_x
        self.curve_target_y = self.next_stop_target_y
        self.curve_target_yaw = self.next_stop_target_yaw
        self._build_bezier_trajectory(
            self.next_stop_start_handle,
            self.next_stop_end_handle,
        )
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = now
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.STATION_TO_NEXT_STOP
        self._publish_media(self.display_mode_pub, 'IMAGE')
        self.get_logger().warning(
            'STATION departure started: saved actual STATION odom pose; '
            f'target=({self.curve_target_x:.3f}, '
            f'{self.curve_target_y:.3f}, '
            f'{math.degrees(self.curve_target_yaw):.1f}deg)')

    def _finish_next_stop(self, path_complete=False):
        self.enabled = False
        self.sequence_active = True
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop(repeat=5)
        suffix = 'Bezier path complete' if path_complete else 'pose tolerance satisfied'
        self.get_logger().warning(
            f'NEXT STOP position reached: {suffix}; '
            'starting final 30deg right rotation')
        self.next_stop_rotate_start_yaw = self.current_yaw
        self.next_stop_rotate_yaw_change = 0.0
        self.next_stop_rotate_started_at = self.get_clock().now()
        self.state = DriveState.NEXT_STOP_FINAL_ROTATE

    def _control_next_stop_final_rotate(self, now):
        elapsed = (
            now - self.next_stop_rotate_started_at).nanoseconds / 1e9
        if elapsed >= self.next_stop_final_rotate_timeout:
            self._enter_fault('next stop final rotation timeout')
            return
        command = Twist()
        command.linear.x = 0.0
        command.angular.z = -self.next_stop_final_rotate_speed
        self.cmd_pub.publish(command)
        self.last_linear_command = 0.0
        self.steering_command = command.angular.z
        self.command_active = True

    def _finish_next_stop_final_rotate(self):
        self.enabled = False
        self.sequence_active = True
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.state = DriveState.NEXT_WAYPOINT_WAIT
        self.next_waypoint_wait_started_at = self.get_clock().now()
        self._publish_stop(repeat=5)
        self.get_logger().warning(
            'final 30deg right rotation complete; waiting 3.5s before '
            'next waypoint Bezier')

    def _control_next_waypoint_wait(self, now):
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop()
        elapsed = (
            now - self.next_waypoint_wait_started_at).nanoseconds / 1e9
        if elapsed < self.next_waypoint_wait:
            return
        self._start_next_waypoint(now)

    def _start_next_waypoint(self, now):
        self.next_waypoint_start_x = self.current_x
        self.next_waypoint_start_y = self.current_y
        self.next_waypoint_start_yaw = self.current_yaw
        cosine = math.cos(self.next_waypoint_start_yaw)
        sine = math.sin(self.next_waypoint_start_yaw)
        local_y = -self.next_waypoint_target_right
        self.next_waypoint_target_x = (
            self.next_waypoint_start_x
            + cosine * self.next_waypoint_target_forward
            - sine * local_y
        )
        self.next_waypoint_target_y = (
            self.next_waypoint_start_y
            + sine * self.next_waypoint_target_forward
            + cosine * local_y
        )
        self.next_waypoint_target_yaw = self._normalize_angle(
            self.next_waypoint_start_yaw
            + self.next_waypoint_target_yaw_relative)
        self.curve_start_x = self.next_waypoint_start_x
        self.curve_start_y = self.next_waypoint_start_y
        self.curve_start_yaw = self.next_waypoint_start_yaw
        self.curve_target_x = self.next_waypoint_target_x
        self.curve_target_y = self.next_waypoint_target_y
        self.curve_target_yaw = self.next_waypoint_target_yaw
        self._build_bezier_trajectory(
            self.next_waypoint_start_handle,
            self.next_waypoint_end_handle,
        )
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = now
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.NEXT_WAYPOINT_MOVE
        self.get_logger().warning(
            'NEXT_WAYPOINT_MOVE: saved actual pose after 3.5s wait; '
            'target=18cm forward / 17cm right / 80deg right')

    def _finish_next_waypoint(self, path_complete=False):
        self.enabled = False
        self.sequence_active = True
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.state = DriveState.NEXT_WAYPOINT_REACHED
        self._publish_stop(repeat=5)
        suffix = 'Bezier path complete' if path_complete else 'pose tolerance satisfied'
        self.get_logger().warning(
            f'NEXT_WAYPOINT_REACHED: {suffix}; STOPPING')
        self._clear_detection()
        self.final_camera_start_x = self.current_x
        self.final_camera_start_y = self.current_y
        self.final_camera_distance = 0.0
        self.state = DriveState.FINAL_CAMERA_DRIVING
        self.get_logger().warning(
            'FINAL_CAMERA_DRIVING: starting 0.60m camera-guided segment')

    def _start_final_straight_drive(self):
        self.final_straight_start_x = self.current_x
        self.final_straight_start_y = self.current_y
        self.final_straight_distance = 0.0
        self.final_straight_started_at = self.get_clock().now()
        self.state = DriveState.FINAL_STRAIGHT_DRIVING
        self.get_logger().warning(
            'FINAL_CAMERA_DRIVING complete at 0.60m; '
            'continuing 0.33m straight without camera steering')

    def _control_final_straight_drive(self, now):
        elapsed = (
            now - self.final_straight_started_at).nanoseconds / 1e9
        if elapsed >= self.final_straight_timeout:
            self._enter_fault('final straight timeout')
            return
        command = Twist()
        command.linear.x = min(self.linear_speed, self.max_linear_speed)
        command.angular.z = 0.0
        self.cmd_pub.publish(command)
        self.last_linear_command = command.linear.x
        self.steering_command = 0.0
        self.command_active = True

    def _finish_final_drive(self):
        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.state = DriveState.FINAL_REACHED
        self._publish_stop(repeat=5)
        self._publish_media(self.music_pub, 'STOP')
        self.get_logger().warning(
            f'FINAL_REACHED: camera={self.final_camera_distance:.3f}m, '
            f'straight={self.final_straight_distance:.3f}m; STOPPING')

    def _start_station_final_approach(self, now):
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop(repeat=3)
        self.station_final_approach_start_x = self.current_x
        self.station_final_approach_start_y = self.current_y
        self.station_final_approach_started_at = now
        self.station_final_approach_distance = 0.0
        self.station_final_approach_best_error = self.curve_position_error
        target_dx = self.curve_target_x - self.current_x
        target_dy = self.curve_target_y - self.current_y
        self.station_final_previous_forward_to_target = (
            math.cos(self.current_yaw) * target_dx
            + math.sin(self.current_yaw) * target_dy
        )
        self.state = DriveState.STATION_FINAL_APPROACH
        self.get_logger().warning(
            'STATION_FINAL_APPROACH: Bezier path exhausted; '
            f'continuing at <= {self.station_final_approach_speed:.3f}m/s')

    def _station_final_command(
            self, position_error, heading_error, yaw_error):
        if position_error <= self.curve_position_tolerance:
            linear = 0.005
        else:
            linear = min(
                self.station_final_approach_speed,
                max(0.005, position_error * 0.3),
            )

        if abs(yaw_error) <= self.curve_yaw_tolerance:
            angular = 0.0
        else:
            if position_error > 0.08:
                yaw_weight = 0.0
            elif position_error <= self.curve_position_tolerance:
                yaw_weight = 1.0
            else:
                yaw_weight = (
                    (0.08 - position_error)
                    / (0.08 - self.curve_position_tolerance)
                )
            steering_error = self._normalize_angle(
                (1.0 - yaw_weight) * heading_error
                + yaw_weight * yaw_error
            )
            angular = max(
                -self.station_final_approach_max_angular,
                min(self.station_final_approach_max_angular,
                    self.curve_kp_yaw * steering_error),
            )
        return linear, angular

    def _station_final_target_passed(self, forward_to_target):
        return (
            self.last_linear_command > 0.0
            and self.station_final_previous_forward_to_target is not None
            and self.station_final_previous_forward_to_target >= 0.0
            and forward_to_target < -self.station_overshoot_tolerance
        )

    def _control_station_final_approach(self, now):
        elapsed = (
            now - self.station_final_approach_started_at).nanoseconds / 1e9
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)

        if self._station_pose_reached():
            self._finish_station()
            return
        if elapsed >= self.station_final_approach_timeout:
            self._enter_fault('station final approach timeout')
            return
        if self.station_final_approach_distance >= self.station_final_approach_max:
            self._enter_fault('station final approach travel limit exceeded')
            return

        target_dx = self.curve_target_x - self.current_x
        target_dy = self.curve_target_y - self.current_y
        target_heading = math.atan2(target_dy, target_dx)
        heading_error = self._normalize_angle(
            target_heading - self.current_yaw)

        if self.curve_position_error < self.station_final_approach_best_error:
            self.station_final_approach_best_error = self.curve_position_error
        elif (
                self.last_linear_command > 0.0
                and
                self.curve_position_error
                > self.station_final_approach_best_error
                + self.station_overshoot_tolerance
        ):
            self._enter_fault('station final approach moving away from target')
            return

        forward_to_target = (
            math.cos(self.current_yaw) * target_dx
            + math.sin(self.current_yaw) * target_dy
        )
        if self._station_final_target_passed(forward_to_target):
            self._enter_fault('station final approach passed target')
            return
        self.station_final_previous_forward_to_target = forward_to_target

        linear, angular = self._station_final_command(
            self.curve_position_error,
            heading_error,
            self.curve_yaw_error,
        )
        command = Twist()
        command.linear.x = linear
        command.angular.z = angular
        self.cmd_pub.publish(command)
        self.last_linear_command = linear
        self.steering_command = angular
        self.command_active = True

    def _prepare_station_target(self, now):
        if self.waypoint_station_mode:
            # In this mode the STATION target must not be computed at STOP.
            # It is computed only from the measured odom pose after the
            # 0.17m straight and 15deg in-place turn are complete.
            self.station_target_x = None
            self.station_target_y = None
            self.station_target_yaw = None
            self.curve_target_x = None
            self.curve_target_y = None
            self.curve_target_yaw = None
            self.curve_points = None
            self.curve_started_at = None
            self.station_wait_started_at = now
            self.state = DriveState.FIRST_POINT_REACHED
            self.get_logger().warning(
                'FIRST_POINT_REACHED: target pose tolerance satisfied; '
                f'STOPPING for {self.station_stop_duration:.1f}s')
            return

        # Legacy modes fix their world-frame targets at STOP/FIRST_POINT.
        self.curve_start_x = self.current_x
        self.curve_start_y = self.current_y
        self.curve_start_yaw = self.current_yaw
        cosine = math.cos(self.curve_start_yaw)
        sine = math.sin(self.curve_start_yaw)
        waypoint_local_y = -self.station_waypoint_right
        self.station_waypoint_x = (
            self.curve_start_x
            + cosine * self.station_waypoint_forward
            - sine * waypoint_local_y
        )
        self.station_waypoint_y = (
            self.curve_start_y
            + sine * self.station_waypoint_forward
            + cosine * waypoint_local_y
        )
        self.station_waypoint_yaw = self._normalize_angle(
            self.curve_start_yaw + self.station_waypoint_yaw_relative)
        local_y = -self.station_target_right
        self.station_target_x = (
            self.curve_start_x
            + cosine * self.station_target_forward
            - sine * local_y
        )
        self.station_target_y = (
            self.curve_start_y
            + sine * self.station_target_forward
            + cosine * local_y
        )
        self.station_target_yaw = self._normalize_angle(
            self.curve_start_yaw + self.station_target_yaw_relative)
        self.curve_target_x = self.station_target_x
        self.curve_target_y = self.station_target_y
        self.curve_target_yaw = self.station_target_yaw
        self.curve_points = None
        self.curve_started_at = None
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.station_wait_started_at = now
        self.state = DriveState.FIRST_POINT_REACHED
        self.get_logger().warning(
            'FIRST_POINT_REACHED: target pose tolerance satisfied; '
            f'STOPPING for {self.station_stop_duration:.1f}s')

    def _start_station_wait(self):
        self.state = DriveState.STATION_WAIT
        self._publish_stop()
        self.get_logger().warning(
            f'STATION_WAIT: holding zero velocity for '
            f'{self.station_stop_duration:.1f}s')

    def _control_station_wait(self, now):
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.command_active = False
        self._publish_stop()
        elapsed = (now - self.station_wait_started_at).nanoseconds / 1e9
        if elapsed < self.station_stop_duration:
            return

        if self.test_forward_mode:
            self._start_test_forward(now)
        elif self.waypoint_forward_rotate_test_mode:
            self._start_waypoint_test_forward(now)
        elif self.waypoint_forward_only_test_mode:
            self._start_waypoint_test_forward(now)
        elif self.waypoint_station_mode:
            self._start_waypoint_test_forward(now)
        elif self.station_direct_mode:
            self._start_direct_station_curve(now)
        elif self.station_waypoint_test_mode:
            self._start_waypoint_test_forward(now)
        else:
            self._start_station_waypoint(now)

    def _start_test_forward(self, now):
        self.test_forward_start_x = self.current_x
        self.test_forward_start_y = self.current_y
        self.test_forward_start_yaw = self.current_yaw
        self.test_forward_distance = 0.0
        self.test_forward_started_at = now
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.command_active = False
        self.state = DriveState.TEST_FORWARD_MOVE
        self._publish_stop()
        self.get_logger().warning(
            f'TEST_FORWARD_MOVE: driving straight '
            f'{self.test_forward_target:.3f}m using odom')

    def _control_test_forward(self, now):
        elapsed = (now - self.test_forward_started_at).nanoseconds / 1e9
        if elapsed >= self.test_forward_timeout:
            self._enter_fault('test forward timeout')
            return
        command = Twist()
        command.linear.x = self.test_forward_speed
        command.angular.z = 0.0
        self.cmd_pub.publish(command)
        self.last_linear_command = command.linear.x
        self.steering_command = 0.0
        self.command_active = True

    def _finish_test_forward(self):
        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.state = DriveState.TEST_FORWARD_REACHED
        self._publish_stop(repeat=5)
        self.get_logger().warning(
            f'TEST_FORWARD_REACHED: {self.test_forward_distance:.3f}m; '
            'STOPPING')

    def _start_waypoint_test_forward(self, now):
        if self.waypoint_forward_rotate_test_mode:
            self.waypoint_motion_forward_distance = (
                self.waypoint_forward_rotate_test_distance)
            self.waypoint_motion_rotate_angle = (
                self.waypoint_forward_rotate_test_angle)
            self.waypoint_motion_rotate_max_angle = (
                self.waypoint_forward_rotate_test_max_angle)
        else:
            self.waypoint_motion_forward_distance = (
                self.waypoint_test_forward_distance)
            self.waypoint_motion_rotate_angle = self.waypoint_test_rotate_angle
            self.waypoint_motion_rotate_max_angle = (
                self.waypoint_test_rotate_max_angle)
        self.waypoint_test_start_x = self.current_x
        self.waypoint_test_start_y = self.current_y
        self.waypoint_test_distance = 0.0
        self.waypoint_test_started_at = now
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.command_active = False
        self.state = DriveState.WAYPOINT_TEST_FORWARD
        self._publish_stop()
        self.get_logger().warning(
            'WAYPOINT_TEST_FORWARD: driving straight '
            f'{self.waypoint_motion_forward_distance:.3f}m using odom')

    def _control_waypoint_test_forward(self, now):
        elapsed = (now - self.waypoint_test_started_at).nanoseconds / 1e9
        if elapsed >= self.waypoint_test_forward_timeout:
            self._enter_fault('waypoint test forward timeout')
            return
        command = Twist()
        command.linear.x = self.waypoint_test_forward_speed
        command.angular.z = 0.0
        self.cmd_pub.publish(command)
        self.last_linear_command = command.linear.x
        self.steering_command = 0.0
        self.command_active = True

    def _finish_waypoint_test_forward(self):
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop(repeat=5)
        if self.waypoint_forward_only_test_mode:
            self.enabled = False
            self.sequence_active = False
            self.state = DriveState.WAYPOINT_FORWARD_ONLY_REACHED
            self.get_logger().warning(
                'TEST_FORWARD_REACHED: '
                f'distance={self.waypoint_test_distance:.3f}m; STOPPING')
            return
        self.waypoint_test_start_yaw = self.current_yaw
        self.waypoint_test_yaw_change = 0.0
        self.waypoint_test_started_at = self.get_clock().now()
        self.state = DriveState.WAYPOINT_TEST_ROTATE
        self.get_logger().warning(
            'WAYPOINT_TEST_FORWARD complete; STOPPED, starting odom yaw turn')

    def _control_waypoint_test_rotate(self, now):
        elapsed = (now - self.waypoint_test_started_at).nanoseconds / 1e9
        if elapsed >= self.waypoint_test_rotate_timeout:
            self._enter_fault('waypoint test rotation timeout')
            return
        command = Twist()
        command.linear.x = 0.0
        command.angular.z = -self.waypoint_test_rotate_speed
        self.cmd_pub.publish(command)
        self.last_linear_command = 0.0
        self.steering_command = command.angular.z
        self.command_active = True

    def _finish_waypoint_test_rotate(self):
        if self.waypoint_forward_rotate_test_mode:
            self.enabled = False
            self.sequence_active = False
            self.command_active = False
            self.last_linear_command = 0.0
            self.steering_command = 0.0
            self.state = DriveState.WAYPOINT_FORWARD_ROTATE_TEST_REACHED
            self._publish_stop(repeat=5)
            self.get_logger().warning(
                'WAYPOINT_FORWARD_ROTATE_TEST_REACHED: '
                f'{self.waypoint_motion_forward_distance:.3f}m straight and '
                f'{math.degrees(self.waypoint_motion_rotate_angle):.1f}deg '
                'right turn; STOPPING')
            return

        if self.waypoint_station_mode:
            self.command_active = False
            self.last_linear_command = 0.0
            self.steering_command = 0.0
            self._publish_stop(repeat=5)
            self.waypoint_settle_started_at = self.get_clock().now()
            self.state = DriveState.WAYPOINT_SETTLE
            self.get_logger().warning(
                'WAYPOINT_SETTLE: rotation complete; holding Zero Twist for '
                f'{self.waypoint_pose_settle_duration:.1f}s before saving odom pose')
            return

        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self.state = DriveState.WAYPOINT_TEST_REACHED
        self._publish_stop(repeat=5)
        self.get_logger().warning(
            'WAYPOINT_TEST_REACHED: '
            f'{self.waypoint_motion_forward_distance:.3f}m straight and '
            f'{math.degrees(self.waypoint_motion_rotate_angle):.1f}deg '
            'right turn; '
            'STOPPING without STATION_MOVE')

    def _control_waypoint_settle(self, now):
        self.command_active = False
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop()
        elapsed = (now - self.waypoint_settle_started_at).nanoseconds / 1e9
        if elapsed < self.waypoint_pose_settle_duration:
            return

        self.waypoint_start_x = self.current_x
        self.waypoint_start_y = self.current_y
        self.waypoint_start_yaw = self.current_yaw
        self.state = DriveState.WAYPOINT_REACHED
        self.get_logger().warning(
            'WAYPOINT_REACHED: saved settled actual odom pose; '
            'starting waypoint-relative STATION path')
        self._prepare_station_from_waypoint()
        self._start_station_from_waypoint(now)

    def _prepare_station_from_waypoint(self):
        cosine = math.cos(self.waypoint_start_yaw)
        sine = math.sin(self.waypoint_start_yaw)
        local_y = -self.station_target_right
        self.station_target_x = (
            self.waypoint_start_x
            + cosine * self.station_target_forward
            - sine * local_y
        )
        self.station_target_y = (
            self.waypoint_start_y
            + sine * self.station_target_forward
            + cosine * local_y
        )
        self.station_target_yaw = self._normalize_angle(
            self.waypoint_start_yaw + self.station_target_yaw_relative)

    def _start_station_from_waypoint(self, now):
        self.curve_start_x = self.waypoint_start_x
        self.curve_start_y = self.waypoint_start_y
        self.curve_start_yaw = self.waypoint_start_yaw
        self.curve_target_x = self.station_target_x
        self.curve_target_y = self.station_target_y
        self.curve_target_yaw = self.station_target_yaw
        self._build_bezier_trajectory(
            self.station_direct_start_handle,
            self.station_direct_end_handle,
        )
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = now
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.STATION_MOVE_FROM_WAYPOINT
        self.get_logger().warning(
            'STATION_MOVE_FROM_WAYPOINT: actual odom waypoint origin, '
            f'target=({self.curve_target_x:.3f}, '
            f'{self.curve_target_y:.3f}, '
            f'{math.degrees(self.curve_target_yaw):.1f}deg)')

    def _start_station_waypoint(self, now):
        self.curve_start_x = self.current_x
        self.curve_start_y = self.current_y
        self.curve_start_yaw = self.current_yaw
        self.curve_target_x = self.station_waypoint_x
        self.curve_target_y = self.station_waypoint_y
        self.curve_target_yaw = self.station_waypoint_yaw
        self._build_bezier_trajectory(
            self.station_waypoint_start_handle,
            self.station_waypoint_end_handle,
        )
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = now
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.STATION_TO_WAYPOINT
        self.get_logger().warning(
            'STATION_TO_WAYPOINT: '
            f'target=({self.curve_target_x:.3f}, '
            f'{self.curve_target_y:.3f}, '
            f'{math.degrees(self.curve_target_yaw):.1f}deg)')

    def _start_direct_station_curve(self, now):
        self.curve_start_x = self.current_x
        self.curve_start_y = self.current_y
        self.curve_start_yaw = self.current_yaw
        self.curve_target_x = self.station_target_x
        self.curve_target_y = self.station_target_y
        self.curve_target_yaw = self.station_target_yaw
        self._build_bezier_trajectory(
            self.station_direct_start_handle,
            self.station_direct_end_handle,
        )
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = now
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.STATION_MOVE
        self.get_logger().warning(
            'STATION_MOVE: direct STOP-relative Bezier, '
            f'target=({self.curve_target_x:.3f}, '
            f'{self.curve_target_y:.3f}, '
            f'{math.degrees(self.curve_target_yaw):.1f}deg)')

    def _finish_station_waypoint(self, now):
        self.state = DriveState.STATION_WAYPOINT_REACHED
        if self.station_waypoint_test_mode:
            self.enabled = False
            self.sequence_active = False
            self.command_active = False
            self.last_linear_command = 0.0
            self.steering_command = 0.0
            self._publish_stop(repeat=5)
            self.get_logger().warning(
                'STATION_WAYPOINT_REACHED: measurement mode complete; '
                'STOPPING without STATION_MOVE')
            return
        self.get_logger().warning(
            'STATION_WAYPOINT_REACHED: pose tolerance satisfied; '
            'continuing smoothly to STATION_MOVE')
        self._start_station_curve(now)

    def _start_station_curve(self, now):
        # The second segment starts at the measured waypoint pose.  Use the
        # waypoint heading as its tangent so both cubic segments are C1-aligned.
        self.curve_start_x = self.current_x
        self.curve_start_y = self.current_y
        self.curve_start_yaw = self.station_waypoint_yaw
        self.curve_target_x = self.station_target_x
        self.curve_target_y = self.station_target_y
        self.curve_target_yaw = self.station_target_yaw
        self._build_bezier_trajectory(
            self.station_start_handle,
            self.station_end_handle,
        )
        self.curve_progress_index = 0
        self.curve_distance = 0.0
        self.curve_started_at = now
        self.curve_position_error = math.hypot(
            self.curve_target_x - self.current_x,
            self.curve_target_y - self.current_y,
        )
        self.curve_yaw_error = self._normalize_angle(
            self.curve_target_yaw - self.current_yaw)
        self.state = DriveState.STATION_MOVE
        self.get_logger().warning(
            'STATION_MOVE: waypoint-to-station Bezier, '
            f'target=({self.curve_target_x:.3f}, '
            f'{self.curve_target_y:.3f}, '
            f'{math.degrees(self.curve_target_yaw):.1f}deg)')

    def _enable_callback(self, request, response):
        if not request.data:
            self._disable()
            response.success = True
            response.message = 'DISABLED and zero velocity published'
            return response

        now = self.get_clock().now()
        if self._is_stale(now, self.last_frame_time, self.frame_timeout):
            response.success = False
            response.message = 'cannot enable: no fresh camera frame'
            return response
        if not self.path_detected:
            response.success = False
            response.message = 'cannot enable: yellow boundary not detected'
            return response
        if self.current_x is None or self._is_stale(
                now, self.last_odom_time, self.odom_timeout):
            response.success = False
            response.message = 'cannot enable: no fresh odom'
            return response

        self.start_x = self.current_x
        self.start_y = self.current_y
        self.odom_distance = 0.0
        self._reset_harvest_action_state()
        self.enabled = True
        self.sequence_active = True
        self.command_active = False
        self.state = DriveState.CAMERA_DRIVING
        response.success = True
        response.message = (
            f'CAMERA_DRIVING armed from odom ({self.start_x:.3f}, '
            f'{self.start_y:.3f})')
        self.get_logger().warning(response.message)
        self._publish_media(self.display_mode_pub, 'IMAGE')
        self._publish_media(self.music_pub, 'START')
        return response

    def _publish_media(self, publisher, text):
        # LCD/music are cosmetic: never let them affect driving.
        try:
            publisher.publish(String(data=text))
        except Exception as error:
            self.get_logger().warning(f'media publish {text} failed: {error}')

    def _disable(self):
        self._publish_media(self.music_pub, 'STOP')
        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.state = DriveState.DISABLED
        self._reset_harvest_action_state()
        self.start_x = None
        self.start_y = None
        self.odom_distance = 0.0
        self.curve_points = None
        self.curve_started_at = None
        self.curve_distance = 0.0
        self.station_wait_started_at = None
        self.station_waypoint_x = None
        self.station_waypoint_y = None
        self.station_waypoint_yaw = None
        self.station_target_x = None
        self.station_target_y = None
        self.station_target_yaw = None
        self.test_forward_start_x = None
        self.test_forward_start_y = None
        self.test_forward_start_yaw = None
        self.test_forward_distance = 0.0
        self.test_forward_started_at = None
        self.waypoint_test_start_x = None
        self.waypoint_test_start_y = None
        self.waypoint_test_start_yaw = None
        self.waypoint_test_distance = 0.0
        self.waypoint_test_yaw_change = 0.0
        self.waypoint_test_started_at = None
        self.waypoint_motion_forward_distance = None
        self.waypoint_motion_rotate_angle = None
        self.waypoint_motion_rotate_max_angle = None
        self.waypoint_start_x = None
        self.waypoint_start_y = None
        self.waypoint_start_yaw = None
        self.station_final_approach_start_x = None
        self.station_final_approach_start_y = None
        self.station_final_approach_started_at = None
        self.station_final_approach_distance = 0.0
        self.station_final_approach_best_error = None
        self.station_final_previous_forward_to_target = None
        self.station_departure_requested.clear()
        self.station_input_active.clear()
        self.station_start_x = None
        self.station_start_y = None
        self.station_start_yaw = None
        self.next_stop_target_x = None
        self.next_stop_target_y = None
        self.next_stop_target_yaw = None
        self.next_stop_rotate_start_yaw = None
        self.next_stop_rotate_yaw_change = 0.0
        self.next_stop_rotate_started_at = None
        self.next_waypoint_wait_started_at = None
        self.next_waypoint_start_x = None
        self.next_waypoint_start_y = None
        self.next_waypoint_start_yaw = None
        self.next_waypoint_target_x = None
        self.next_waypoint_target_y = None
        self.next_waypoint_target_yaw = None
        self.final_camera_start_x = None
        self.final_camera_start_y = None
        self.final_camera_distance = 0.0
        self.final_straight_start_x = None
        self.final_straight_start_y = None
        self.final_straight_distance = 0.0
        self.final_straight_started_at = None
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop(repeat=3)
        self.get_logger().info('camera drive DISABLED')

    def _enter_fault(self, reason):
        if self.state == DriveState.FAULT:
            return
        self.station_departure_requested.clear()
        self.station_input_active.clear()
        self._reset_harvest_action_state()
        self.enabled = False
        self.sequence_active = False
        self.command_active = False
        self.state = DriveState.FAULT
        self.last_linear_command = 0.0
        self.steering_command = 0.0
        self._publish_stop(repeat=5)
        self.get_logger().error(f'FAULT: {reason}; STOPPING')

    def _log_status_if_due(self):
        now = self.get_clock().now()
        elapsed = (now - self.last_frame_log_time).nanoseconds / 1e9
        interval = float(
            self.get_parameter('frame_log_interval_sec').value)
        if elapsed < interval:
            return
        if self.state == DriveState.STATION_FINAL_APPROACH:
            self.get_logger().info(
                f'state={self.state}, '
                f'final_distance={self.station_final_approach_distance:.3f}, '
                f'current_x={self.current_x:.3f}, current_y={self.current_y:.3f}, '
                f'current_yaw={math.degrees(self.current_yaw):.1f}deg, '
                f'target_x={self.curve_target_x:.3f}, '
                f'target_y={self.curve_target_y:.3f}, '
                f'target_yaw={math.degrees(self.curve_target_yaw):.1f}deg, '
                f'position_error={self.curve_position_error:.3f}, '
                f'yaw_error={math.degrees(self.curve_yaw_error):.1f}deg, '
                f'linear.x={self.last_linear_command:.3f}, '
                f'angular.z={self.steering_command:.3f}')
        elif self.state in (
                DriveState.CURVE_TO_FIRST_POINT,
                DriveState.STATION_TO_WAYPOINT,
                DriveState.STATION_MOVE,
                DriveState.STATION_MOVE_FROM_WAYPOINT,
        ):
            self.get_logger().info(
                f'state={self.state}, curve_distance={self.curve_distance:.3f}, '
                f'current_x={self.current_x:.3f}, current_y={self.current_y:.3f}, '
                f'current_yaw={math.degrees(self.current_yaw):.1f}deg, '
                f'target_x={self.curve_target_x:.3f}, '
                f'target_y={self.curve_target_y:.3f}, '
                f'target_yaw={math.degrees(self.curve_target_yaw):.1f}deg, '
                f'position_error={self.curve_position_error:.3f}, '
                f'yaw_error={math.degrees(self.curve_yaw_error):.1f}deg, '
                f'linear.x={self.last_linear_command:.3f}, '
                f'angular.z={self.steering_command:.3f}')
        elif self.state in (
                DriveState.FIRST_POINT_REACHED,
                DriveState.STATION_WAIT,
        ):
            wait_elapsed = (
                now - self.station_wait_started_at).nanoseconds / 1e9
            wait_remaining = max(
                0.0, self.station_stop_duration - wait_elapsed)
            self.get_logger().info(
                f'state={self.state}, enabled={self.enabled}, '
                f'sequence_active={self.sequence_active}, '
                f'station_wait_remaining={wait_remaining:.2f}s, '
                'linear.x=0.000, angular.z=0.000')
        elif self.state in (
                DriveState.TEST_FORWARD_MOVE,
                DriveState.TEST_FORWARD_REACHED,
        ):
            self.get_logger().info(
                f'state={self.state}, enabled={self.enabled}, '
                f'sequence_active={self.sequence_active}, '
                f'test_distance={self.test_forward_distance:.3f}m, '
                f'test_target={self.test_forward_target:.3f}m, '
                f'linear.x={self.last_linear_command:.3f}, '
                'angular.z=0.000')
        elif self.state in (
                DriveState.WAYPOINT_TEST_FORWARD,
                DriveState.WAYPOINT_FORWARD_ONLY_REACHED,
        ):
            self.get_logger().info(
                'TEST_FORWARD: '
                f'distance={self.waypoint_test_distance:.3f}m, '
                f'linear.x={self.last_linear_command:.3f}, '
                'angular.z=0.000')
        else:
            self.get_logger().info(
                f'state={self.state}, enabled={self.enabled}, '
                f'frames={self.frame_count}, distance={self.odom_distance:.3f}m, '
                f'boundary_x={self.boundary_x}, target_x={self.target_x}, '
                f'error={self.path_error}, angular.z={self.steering_command:.3f}, '
                f'path={self.path_detected}')
        self.frame_count = 0
        self.last_frame_log_time = now

    @staticmethod
    def _is_stale(now, stamp, timeout):
        return stamp is None or (now - stamp).nanoseconds / 1e9 > timeout

    @staticmethod
    def _normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def _yaw_from_quaternion(x, y, z, w):
        sin_yaw = 2.0 * (w * z + x * y)
        cos_yaw = 1.0 - 2.0 * (y * y + z * z)
        return math.atan2(sin_yaw, cos_yaw)

    def _publish_stop(self, repeat=1):
        stop = Twist()
        for _ in range(repeat):
            self.cmd_pub.publish(stop)

    def _publish_drive_state(self):
        message = String()
        message.data = self.state
        self.state_pub.publish(message)

    def destroy_node(self):
        self.harvest_shutting_down = True
        if (hasattr(self, 'harvest_goal_handle')
                and self.harvest_goal_handle is not None
                and self.harvest_goal_accepted
                and not self.harvest_result_received):
            try:
                self.harvest_goal_handle.cancel_goal_async()
            except Exception:
                pass
        if hasattr(self, 'station_input_shutdown'):
            self.station_input_shutdown.set()
            self.station_input_active.set()
        if (hasattr(self, 'station_input_thread')
                and self.station_input_thread.is_alive()):
            self.station_input_thread.join(timeout=1.0)
        if hasattr(self, 'cmd_pub') and rclpy.ok():
            self._publish_stop(repeat=5)
        if hasattr(self, 'music_pub') and rclpy.ok():
            self._publish_media(self.music_pub, 'STOP')
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = CameraStraightDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node._publish_stop(repeat=5)
            rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
