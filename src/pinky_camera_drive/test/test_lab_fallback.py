"""Lab b* fallback: catches a shadowed yellow line HSV misses, rejects orange."""

import pathlib
import types

import cv2
import numpy as np
import yaml

from pinky_camera_drive import camera_straight_drive as drive

Drive = drive.CameraStraightDrive
CONFIG = pathlib.Path(__file__).resolve().parents[1] / 'config' / 'camera_straight_drive.yaml'
PARAMS = yaml.safe_load(CONFIG.read_text())['camera_straight_drive']['ros__parameters']


def make_node(fallback=True):
    node = types.SimpleNamespace(
        state=drive.DriveState.DISABLED,
        hsv_adaptive_enabled=False,
        yellow_lab_fallback_enabled=fallback,
        line_source=None,
        path_detected=False,
        steering_command=0.0,
        target_x_config=float(PARAMS['target_x']),
        steering_sign=float(PARAMS['steering_sign']),
        kp=float(PARAMS['kp']),
        max_angular_speed=float(PARAMS['max_angular_speed']),
        logs=[],
    )
    for key in ('roi_top_ratio', 'roi_left_ratio', 'roi_right_ratio',
                'min_boundary_area', 'min_boundary_height_ratio',
                'min_line_points',
                'boundary_eval_y_ratio', 'boundary_reference_x',
                'yellow_lab_b_low', 'yellow_lab_a_high'):
        setattr(node, key, PARAMS[key])
    node.line_fit_max_residual = PARAMS.get('line_fit_max_residual_px', 12.0)
    node.get_parameter = lambda name: types.SimpleNamespace(value=PARAMS[name])
    node.get_logger = lambda: types.SimpleNamespace(warning=node.logs.append)
    for name in ('_detect_yellow_boundary', '_fit_boundary', '_lab_yellow_mask',
                 '_clear_detection', '_set_camera_steering', '_in_second_next_stop'):
        setattr(node, name, getattr(Drive, name).__get__(node))
    return node


def frame_with_stripe(hsv_color):
    """640x480 grey floor with a vertical stripe of the given HSV colour."""
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)  # grey floor
    stripe = cv2.cvtColor(np.uint8([[hsv_color]]), cv2.COLOR_HSV2BGR)[0, 0]
    frame[:, 100:140] = stripe
    return frame


SHADOWED_YELLOW = (27, 150, 100)  # V 100 < yellow_v_low: HSV misses it


def test_hsv_misses_shadowed_line_without_fallback():
    node = make_node(fallback=False)
    node._detect_yellow_boundary(frame_with_stripe(SHADOWED_YELLOW))
    assert not node.path_detected


def test_lab_fallback_finds_shadowed_line():
    node = make_node()
    node._detect_yellow_boundary(frame_with_stripe(SHADOWED_YELLOW))
    assert node.path_detected and node.line_source == 'LAB'
    assert abs(node.boundary_x - 139) <= 2  # road-facing (right) edge
    assert node.logs == ['yellow line source: LAB']


def test_normal_line_still_uses_hsv():
    node = make_node()
    node._detect_yellow_boundary(frame_with_stripe((27, 150, 165)))
    assert node.path_detected and node.line_source == 'HSV'


def test_lab_fallback_rejects_orange_and_grey():
    for color in ((10, 220, 220), (0, 0, 200)):  # orange, bright grey
        node = make_node()
        node._detect_yellow_boundary(frame_with_stripe(color))
        assert not node.path_detected, color
