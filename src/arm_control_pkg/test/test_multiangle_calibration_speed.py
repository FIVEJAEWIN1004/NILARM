"""Tool-local speed tests for multi-angle XY calibration."""

import json
import inspect

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest.tools import (
    pumpkin_multiangle_xy_micro_adjust as adjust,
)
from arm_control_pkg.pumpkin_harvest.tools import (
    pumpkin_multiangle_xyz_grid_adjust as grid_adjust,
)


def test_calibration_duration_is_twice_as_fast():
    assert adjust.CALIBRATION_SPEED_MULTIPLIER == pytest.approx(2.0)
    assert adjust.calibration_duration(12.0) == pytest.approx(6.0)
    assert adjust.calibration_duration(3.0) == pytest.approx(1.5)


def test_camera_angle_moves_are_four_times_original_speed(monkeypatch):
    monkeypatch.setattr(adjust.multi, "movement_duration", lambda _angle: 24.0)
    assert adjust.ANGLE_MOVE_SPEED_MULTIPLIER == pytest.approx(4.0)
    assert adjust.angle_move_duration(120.0) == pytest.approx(6.0)


def test_calibration_angles_match_competition_scan(monkeypatch):
    assert adjust.CALIBRATION_OFFSETS_DEG == (
        -140, -110, -80, -50, 70, 100, 130
    )
    answers = iter(["0", "70"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert adjust.ask_calibration_offset() == pytest.approx(70.0)


def test_z_jog_step_is_always_two_mm():
    assert adjust.Z_STEP_M == pytest.approx(0.002)


def test_calibration_keeps_only_move_grasp_confirmation():
    source = inspect.getsource(grid_adjust.calibrate_one_sample)
    assert "PREALIGN 입력" not in source
    assert 'MOVE_HIGH 입력' not in source
    assert 'MOVE_30 입력' not in source
    assert "confirm_move_to_grasp()" in source
    assert "bypass_high_delta_guard=True" in source


def test_grid_session_can_finish_selected_slots_without_all_nine():
    source = inspect.getsource(grid_adjust.main)
    assert 'command in {"D", "DONE"}' in source
    assert "while ready_for_verification" in source
    assert 'command in {"R", "RECALIBRATE"}' in source
    assert "recalibrate_only_slots = set(done)" in source
    assert "미저장 칸 추가는 Enter" in source


def test_recalibration_mode_rejects_an_unsaved_slot_before_arm_motion():
    source = inspect.getsource(grid_adjust.calibrate_one_sample)
    rejection = source.index("grid_slot not in recalibrate_only_slots")
    first_move = source.index("arm.move_joints")
    assert rejection < first_move


def test_completed_grid_can_recalibrate_or_start_verification():
    source = inspect.getsource(grid_adjust.main)
    assert 'command in {"V", "VERIFY"}' in source
    assert 'command not in {"R", "RECALIBRATE"}' in source
    assert "기존 값이 교체됩니다" in source


def test_completed_grid_runs_real_grasp_verification():
    source = inspect.getsource(grid_adjust.verify_saved_grid)
    assert grid_adjust.VERIFY_LIFT_M == pytest.approx(0.030)
    assert "검증 물체가 확인되어 자동 파지를 시작합니다" in source
    assert "arm.close_gripper" in source
    assert "arm.open_gripper" in source
    assert "z_offset + VERIFY_LIFT_M" in source
    assert "ask_verification_result" not in source


def test_next_verification_continues_on_enter(monkeypatch):
    answers = iter(["WRONG", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert grid_adjust.ask_next_verification()


def test_next_verification_only_stops_on_explicit_q(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "q")
    assert not grid_adjust.ask_next_verification()


def test_single_key_jog_shortcuts_keep_long_commands_compatible():
    expected = {
        "W": "TOWARD_BASE", "X": "AWAY_BASE",
        "A": "BASE_LEFT", "D": "BASE_RIGHT",
        "R": "Z_UP", "F": "Z_DOWN", "2": "STEP_2",
        "5": "STEP_5", "U": "UNDO", "S": "SAVE", "Q": "Q",
    }
    for key, command in expected.items():
        assert adjust.normalize_jog_command(key) == command
        assert adjust.normalize_jog_command(command) == command


def test_grid_session_requires_three_successful_grasp_verifications():
    source = inspect.getsource(grid_adjust.main)
    assert grid_adjust.REQUIRED_VERIFICATION_PASSES == 3
    assert "verification_passes += 1" in source
    assert "verification_passes >= REQUIRED_VERIFICATION_PASSES" in source


def test_grid_session_tracks_completed_slots(tmp_path, monkeypatch):
    path = tmp_path / "residual.json"
    path.write_text(
        '{"method":"per_angle_manual_world_jog_v1","angles":'
        '{"70":{"samples":[{"grid_slot":1},{"grid_slot":5},'
        '{"grid_slot":9}]}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(adjust.multi, "ANGLE_RESIDUAL_PATH", path)
    assert grid_adjust.completed_slots(70) == [1, 5, 9]


def test_pixel_is_assigned_to_three_by_three_grid():
    image_points = np.asarray([
        [100.0, 50.0], [400.0, 50.0], [400.0, 350.0], [100.0, 350.0]
    ])
    assert adjust.grid_slot_for_pixel((120.0, 70.0), image_points) == (
        1, "왼쪽 위"
    )
    assert adjust.grid_slot_for_pixel((250.0, 200.0), image_points) == (
        5, "화면 중앙"
    )
    assert adjust.grid_slot_for_pixel((390.0, 340.0), image_points) == (
        9, "오른쪽 아래"
    )


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
        5,
    )

    assert record["grasp_z_residual_mm"] == pytest.approx(-7.0)
    assert record["sample_count"] == 1
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["angles"]["-110"]["grasp_z_residual_m"] == pytest.approx(-0.007)
    assert saved["angles"]["-110"]["samples"][0]["grid_slot"] == 5


def test_save_residual_replaces_only_same_grid_slot(tmp_path, monkeypatch):
    path = tmp_path / "residual.json"
    monkeypatch.setattr(adjust.multi, "ANGLE_RESIDUAL_PATH", path)
    args = (-110, -109.5, (100.0, 100.0), np.zeros(2), np.zeros(2))
    adjust.save_residual(*args, -0.002, 1)
    adjust.save_residual(*args, -0.004, 1)
    record = adjust.save_residual(*args, 0.006, 9)

    assert record["sample_count"] == 2
    samples = {item["grid_slot"]: item for item in record["samples"]}
    assert samples[1]["grasp_z_residual_m"] == pytest.approx(-0.004)
    assert samples[9]["grasp_z_residual_m"] == pytest.approx(0.006)
