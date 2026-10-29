"""Selective competition scan-speed tests."""

import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_auto_scan_count_orange_harvest as scan,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


def test_scan_rotation_is_1_3x_faster_than_current_transit():
    transit_seconds = speed.transit_rotation_duration(30)
    scan_seconds = speed.scan_rotation_duration(30)

    assert transit_seconds == pytest.approx(3.6)
    assert scan_seconds == pytest.approx(transit_seconds / 1.3)


def test_speed_configuration_separates_scan_from_other_rotations(monkeypatch):
    monkeypatch.setattr(scan.base, "CAMERA_MOVE_DURATION_SEC", 6.0)
    monkeypatch.setattr(scan.grasp, "HIGH_MOVE_DURATION_SEC", 12.0)
    monkeypatch.setattr(scan.grasp, "LOWER_MOVE_DURATION_SEC", 8.0)
    monkeypatch.setattr(scan.grasp, "LIFT_STEP_DURATION_SEC", 4.0)
    monkeypatch.setattr(scan.grasp, "RETURN_DURATION_SEC", 12.0)
    monkeypatch.setattr(scan.multi, "movement_duration", lambda _delta: 999.0)
    monkeypatch.setattr(scan, "scan_movement_duration", lambda _delta: 999.0)

    speed.configure_selective_speed()

    assert scan.base.CAMERA_MOVE_DURATION_SEC == pytest.approx(3.6)
    assert scan.multi.movement_duration is speed.transit_rotation_duration
    assert scan.scan_movement_duration is speed.scan_rotation_duration
