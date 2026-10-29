"""First scan entry and pumpkin preposition speed tests."""

import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as harvest,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as speed,
)


def test_first_minus_140_scan_entry_is_twice_current_scan_speed():
    current = speed.scan_rotation_duration(-140.0)
    accelerated = speed.scan_target_rotation_duration(-140.0, -140.0)

    assert accelerated == pytest.approx(current / 2.0)


def test_other_scan_targets_keep_current_scan_speed():
    assert speed.scan_target_rotation_duration(-110.0, 30.0) == pytest.approx(
        speed.scan_rotation_duration(30.0)
    )
    assert speed.scan_target_rotation_duration(130.0, 30.0) == pytest.approx(
        speed.scan_rotation_duration(30.0)
    )


def test_pumpkin_preposition_is_twice_current_speed():
    assert harvest.PUMPKIN_PREPOSITION_SPEED_MULTIPLIER == pytest.approx(2.0)
    assert harvest.pumpkin_preposition_duration(7.2) == pytest.approx(3.6)
    assert harvest.pumpkin_preposition_duration(4.8) == pytest.approx(2.4)
