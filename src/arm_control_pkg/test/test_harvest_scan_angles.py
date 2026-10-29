"""Competition scan-angle selection tests."""

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_auto_scan_count_orange_harvest as scan,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_multiangle_approach_validation as multi,
)


def test_competition_scan_uses_only_required_views():
    assert scan.SCAN_OFFSETS_DEG == (-140, -110, -80, -50, 70, 100, 130)


def test_skipped_views_remain_available_for_calibration():
    skipped = {-20, 0, 10, 40, 140}
    assert skipped.isdisjoint(scan.SCAN_OFFSETS_DEG)
    assert skipped.issubset(multi.ALLOWED_OFFSETS_DEG)
    assert set(scan.SCAN_OFFSETS_DEG).issubset(multi.ALLOWED_OFFSETS_DEG)
