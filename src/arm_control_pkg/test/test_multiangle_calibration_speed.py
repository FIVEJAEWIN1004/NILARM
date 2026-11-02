"""Tool-local speed tests for multi-angle XY calibration."""

import json

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest.tools import (
    pumpkin_multiangle_xy_micro_adjust as adjust,
)


def test_calibration_duration_is_twice_as_fast():
    assert adjust.CALIBRATION_SPEED_MULTIPLIER == pytest.approx(2.0)
    assert adjust.calibration_duration(12.0) == pytest.approx(6.0)
    assert adjust.calibration_duration(3.0) == pytest.approx(1.5)


def test_calibration_angles_match_competition_scan(monkeypatch):
    assert adjust.CALIBRATION_OFFSETS_DEG == (
        -140, -110, -80, -50, 70, 100, 130
    )
    answers = iter(["0", "70"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert adjust.ask_calibration_offset() == pytest.approx(70.0)


def test_z_jog_step_is_always_two_mm():
    assert adjust.Z_STEP_M == pytest.approx(0.002)


@pytest.mark.parametrize("duration", [0.0, -1.0])
def test_calibration_duration_rejects_non_positive_values(duration):
    with pytest.raises(ValueError):
        adjust.calibration_duration(duration)


def test_save_residual_writes_xyz(tmp_path, monkeypatch):
    path = tmp_path / "residual.json"
    monkeypatch.setattr(adjust.multi, "ANGLE_RESIDUAL_PATH", path)

    record = adjust.save_residual(
        -110,
        -109.5,
        (320.0, 240.0),
        np.asarray([0.001, -0.002]),
        np.asarray([0.002, 0.001]),
        -0.007,
    )

    assert record["grasp_z_residual_mm"] == pytest.approx(-7.0)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["angles"]["-110"]["grasp_z_residual_m"] == pytest.approx(-0.007)
