"""Per-angle grasp-height residual tests for competition harvesting."""

import numpy as np
import pytest
from types import SimpleNamespace

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as harvest,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_multiangle_approach_validation as multi,
)


def make_target():
    return {
        "planned_grasp_z": 0.100,
        "xyz_stages": [
            np.asarray([0.2, 0.1, z], dtype=float)
            for z in (0.180, 0.130, 0.110, 0.100)
        ],
    }


def make_cluster(*angles):
    return SimpleNamespace(
        observations=[
            SimpleNamespace(commanded_offset_deg=angle) for angle in angles
        ]
    )


@pytest.mark.parametrize(
    ("angle", "expected_offset"),
    [(-140, -0.025), (70, 0.005), (130, -0.018), (-110, 0.0)],
)
def test_angle_grasp_z_offset(angle, expected_offset, monkeypatch):
    monkeypatch.setattr(multi, "load_angle_z_residuals", lambda: {})
    original = make_target()
    adjusted = harvest.apply_angle_grasp_z_offset(original, angle)

    assert adjusted["angle_grasp_z_offset_m"] == pytest.approx(expected_offset)
    assert adjusted["planned_grasp_z"] == pytest.approx(
        original["planned_grasp_z"] + expected_offset
    )
    for original_stage, adjusted_stage in zip(
        original["xyz_stages"], adjusted["xyz_stages"]
    ):
        assert adjusted_stage[2] == pytest.approx(
            original_stage[2] + expected_offset
        )

    # The stored detection target must remain unchanged for other consumers.
    assert original["planned_grasp_z"] == pytest.approx(0.100)
    assert [stage[2] for stage in original["xyz_stages"]] == pytest.approx(
        [0.180, 0.130, 0.110, 0.100]
    )


def test_saved_z_residual_overrides_legacy_value(tmp_path, monkeypatch):
    path = tmp_path / "residual.json"
    path.write_text(
        '{"method":"per_angle_manual_world_jog_v1","angles":'
        '{"-140":{"local_residual_m":[0.0,0.0],'
        '"grasp_z_residual_m":-0.031}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(multi, "ANGLE_RESIDUAL_PATH", path)

    adjusted = harvest.apply_angle_grasp_z_offset(make_target(), -140)

    assert adjusted["angle_grasp_z_offset_m"] == pytest.approx(-0.031)


def spatial_sample(slot, u, v, x, y, z):
    return {
        "grid_slot": slot,
        "pixel": np.asarray([u, v], dtype=float),
        "xy": np.asarray([x, y], dtype=float),
        "z": z,
    }


def test_screen_position_interpolates_xyz_inside_sample_hull():
    samples = {70: [
        spatial_sample(
            row * 3 + column + 1,
            column * 50,
            row * 50,
            column * 0.005,
            row * 0.010,
            (row + column) * 0.005,
        )
        for row in range(3)
        for column in range(3)
    ]}

    xy, z, used = multi.spatial_xyz_residual(
        70, (50, 50), np.asarray([0.1, 0.1]), 0.1,
        samples_by_angle=samples,
    )

    assert used
    assert xy == pytest.approx([0.005, 0.010])
    assert z == pytest.approx(0.010)


def test_screen_position_outside_sample_hull_uses_fallback():
    samples = {70: [
        spatial_sample(
            row * 3 + column + 1,
            column * 50,
            row * 50,
            0.001 * column,
            0.001 * row,
            0.001 * (row + column),
        )
        for row in range(3)
        for column in range(3)
    ]}
    fallback_xy = np.asarray([0.003, -0.004])

    xy, z, used = multi.spatial_xyz_residual(
        70, (120, 120), fallback_xy, -0.005,
        samples_by_angle=samples,
    )

    assert not used
    assert xy == pytest.approx(fallback_xy)
    assert z == pytest.approx(-0.005)


def test_apply_height_prefers_spatial_z():
    target = make_target()
    target["spatial_grasp_z_residual_m"] = 0.012

    adjusted = harvest.apply_angle_grasp_z_offset(target, 70)

    assert adjusted["angle_grasp_z_offset_m"] == pytest.approx(0.012)


@pytest.mark.parametrize(
    ("observed_angles", "selected_angle", "expected_angle"),
    [
        ((-140, -110), -110, -140),
        ((100, 130), 100, 130),
        ((70, 100), 100, 70),
        ((-110, -80), -110, -110),
        # Ambiguous clusters with multiple calibrated views keep the actual
        # selected view rather than choosing an arbitrary height correction.
        ((70, 100, 130), 100, 100),
    ],
)
def test_unique_calibrated_observation_selects_height_correction(
    observed_angles,
    selected_angle,
    expected_angle,
    monkeypatch,
):
    monkeypatch.setattr(multi, "load_angle_z_residuals", lambda: {})
    cluster = make_cluster(*observed_angles)
    assert harvest.select_grasp_z_correction_angle(
        cluster,
        selected_angle,
    ) == expected_angle
