"""Tool-local speed tests for multi-angle XY calibration."""

import pytest

from arm_control_pkg.pumpkin_harvest.tools import (
    pumpkin_multiangle_xy_micro_adjust as adjust,
)


def test_calibration_duration_is_twice_as_fast():
    assert adjust.CALIBRATION_SPEED_MULTIPLIER == pytest.approx(2.0)
    assert adjust.calibration_duration(12.0) == pytest.approx(6.0)
    assert adjust.calibration_duration(3.0) == pytest.approx(1.5)


@pytest.mark.parametrize("duration", [0.0, -1.0])
def test_calibration_duration_rejects_non_positive_values(duration):
    with pytest.raises(ValueError):
        adjust.calibration_duration(duration)
