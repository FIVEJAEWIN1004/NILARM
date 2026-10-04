"""Pure-logic tests for hsv_utils (no ROS, camera or GUI needed).

    python3 -m pytest src/pinky_camera_drive/test/test_hsv_utils.py
"""

import datetime
import os
import sys

import numpy as np
import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pinky_camera_drive import hsv_utils as hu  # noqa: E402

RNG = np.random.default_rng(0)


def yellow_pixels(n, h=28, s=160, v=190, spread=(2, 15, 15)):
    noise = RNG.normal(0, 1, (n, 3)) * spread
    return np.clip(np.array([h, s, v]) + noise, 0, 255).astype(np.uint8)


def test_patch_size_and_bounds():
    hsv = np.zeros((20, 30, 3), np.uint8)
    assert hu.sample_patch(hsv, 15, 10, 11).shape == (121, 3)
    assert hu.sample_patch(hsv, 0, 0, 11).shape == (36, 3)  # 6x6 in-bounds corner
    assert hu.sample_patch(hsv, 29, 19, 11).shape == (36, 3)
    assert hu.sample_patch(hsv, -50, 5, 11).shape == (0, 3)


def test_click_plausibility():
    assert hu.is_plausible_yellow(yellow_pixels(121))[0]
    assert not hu.is_plausible_yellow(yellow_pixels(121, h=100))[0]  # blue
    assert not hu.is_plausible_yellow(yellow_pixels(121, s=10))[0]   # white
    assert not hu.is_plausible_yellow(np.empty((0, 3), np.uint8))[0]


def test_bounds_cover_samples_and_stay_yellow():
    pixels = yellow_pixels(5 * 121)
    lower, upper = hu.robust_hsv_bounds(pixels)
    hu.validate_bounds(lower, upper)
    assert hu.H_GUARD[0] <= lower[0] < 28 < upper[0] <= hu.H_GUARD[1]
    assert upper[0] - lower[0] <= 16  # H stays tight
    assert hu.in_range_fraction(pixels, lower, upper) > 0.97
    # S/V get wider margins than H.
    assert upper[2] - lower[2] > upper[0] - lower[0]


def test_outliers_do_not_stretch_range():
    good = yellow_pixels(5 * 121)
    lower, upper = hu.robust_hsv_bounds(good)
    # One click on red, one on green, plus 3% specular white pixels.
    bad = np.vstack([
        good,
        yellow_pixels(121, h=5),
        yellow_pixels(121, h=60),
        np.tile([28, 5, 255], (20, 1)).astype(np.uint8),
    ])
    lower2, upper2 = hu.robust_hsv_bounds(bad)
    assert abs(int(lower2[0]) - int(lower[0])) <= 2
    assert abs(int(upper2[0]) - int(upper[0])) <= 2
    assert lower2[1] >= hu.S_LOW_FLOOR


def test_off_hue_tail_inside_guard_rejected_by_mad():
    # A click on an orange-ish object (H 17) next to yellow H 30 samples.
    pixels = np.vstack([yellow_pixels(600, h=30, spread=(1, 10, 10)),
                        yellow_pixels(80, h=17, spread=(0.5, 10, 10))])
    lower, upper = hu.robust_hsv_bounds(pixels)
    assert lower[0] > 17


def test_bounds_clamped_and_invalid_rejected():
    lower, upper = hu.robust_hsv_bounds(yellow_pixels(600, s=250, v=250))
    assert upper[1] <= 255 and upper[2] <= 255
    with pytest.raises(ValueError):
        hu.robust_hsv_bounds(yellow_pixels(600, h=100))
    for lo, hi in (([30, 50, 50], [25, 200, 200]),   # H inverted
                   ([5, 50, 50], [30, 200, 200]),    # outside guard
                   ([28, 50, 50], [30, 200, 200]),   # H too narrow
                   ([22, 200, 50], [35, 100, 200])):  # S inverted
        with pytest.raises(ValueError):
            hu.validate_bounds(lo, hi)


def test_adaptive_offsets_bounded_and_h_fixed():
    lower = np.array([22, 100, 80], np.uint8)
    upper = np.array([35, 190, 220], np.uint8)
    assert hu.adaptive_sv_offsets(120, 120, 20, 35) == (0, 0, 0)
    # Much darker: only V_low drops, clamped.
    s, vl, vh = hu.adaptive_sv_offsets(20, 120, 20, 35)
    assert (s, vl, vh) == (0, -35, 0)
    # Much brighter: V_high up and S_low down, clamped.
    s, vl, vh = hu.adaptive_sv_offsets(250, 120, 20, 35)
    assert (s, vl, vh) == (-20, 0, 35)
    lo, hi = hu.apply_sv_offsets(lower, upper, s, vl, vh)
    assert (lo[0], hi[0]) == (22, 35)
    assert (lo[1], hi[1], lo[2], hi[2]) == (80, 190, 80, 255)
    lo, hi = hu.apply_sv_offsets(lower, upper, -200, -200, 0)
    assert lo[1] == 0 and lo[2] == 0 and lo.dtype == np.uint8


def test_brightness_and_ema():
    frame = np.full((100, 50, 3), 40, np.uint8)
    frame[70:] = (10, 200, 30)  # bright lower area, V = max channel
    assert hu.scene_brightness(frame, 0.70) == 200
    assert hu.ema_update(None, 100, 0.1) == 100
    assert hu.ema_update(100, 200, 0.1) == pytest.approx(110)


YAML = """camera_straight_drive:
  ros__parameters:
    kp: 0.002
    # keep this comment
    yellow_h_low: 22
    yellow_h_high: 35   # trailing comment
    yellow_s_low: 100
    yellow_s_high: 190
    yellow_v_low: 80
    yellow_v_high: 220
    min_line_points: 25
"""
NEW = dict(zip(hu.HSV_KEYS, (20, 38, 70, 240, 60, 255)))


def test_yaml_update_only_six_keys(tmp_path):
    path = tmp_path / 'c.yaml'
    path.write_text(YAML)
    now = datetime.datetime(2026, 10, 4, 12, 0, 0)
    old, backup = hu.update_hsv_yaml(str(path), NEW, now=now)
    assert old['yellow_v_low'] == 80
    assert backup.endswith('c.yaml.bak_hsv_20261004_120000')
    assert open(backup).read() == YAML
    text = path.read_text()
    assert '# keep this comment' in text
    assert 'yellow_h_high: 38   # trailing comment' in text
    params = yaml.safe_load(text)['camera_straight_drive']['ros__parameters']
    assert {k: params[k] for k in hu.HSV_KEYS} == NEW
    assert params['kp'] == 0.002 and params['min_line_points'] == 25
    assert len(text.splitlines()) == len(YAML.splitlines())


def test_yaml_update_failure_leaves_file(tmp_path):
    path = tmp_path / 'c.yaml'
    duplicated = YAML + '    yellow_v_low: 81\n'
    path.write_text(duplicated)
    with pytest.raises(ValueError):
        hu.update_hsv_yaml(str(path), NEW)
    assert path.read_text() == duplicated
    assert os.listdir(tmp_path) == ['c.yaml']  # no backup, no temp file
    with pytest.raises(ValueError):
        hu.update_hsv_yaml(str(path), {'yellow_h_low': 1})
