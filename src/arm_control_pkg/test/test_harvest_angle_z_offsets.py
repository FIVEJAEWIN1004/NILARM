"""Per-angle grasp-height residual tests for competition harvesting."""

import numpy as np
import pytest
from types import SimpleNamespace

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as harvest,
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
def test_angle_grasp_z_offset(angle, expected_offset):
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
):
    cluster = make_cluster(*observed_angles)
    assert harvest.select_grasp_z_correction_angle(
        cluster,
        selected_angle,
    ) == expected_angle
