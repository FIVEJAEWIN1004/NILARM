#!/usr/bin/env python3
"""Competition-output version of the v4 full-auto orange harvester.

After full-angle scanning and duplicate removal, ripe pumpkins are divided by
OMX base Y: positive Y is zone A and negative Y is zone B.  The mandatory
competition line is printed exactly as ``A-N / B-N`` before Enter starts the
harvest.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from . import pumpkin_auto_scan_count_orange_harvest as scan
from . import pumpkin_full_auto_orange_harvest_to_bin_v2 as v2
from . import pumpkin_full_auto_orange_harvest_to_bin_v4 as v4


# Existing A/B convention: +joint1 / +robot-Y side is A, -Y side is B.
A_IS_POSITIVE_Y = True


def zone_for_cluster(cluster: scan.PumpkinCluster) -> str:
    if A_IS_POSITIVE_Y:
        return "A" if float(cluster.y) >= 0.0 else "B"
    return "A" if float(cluster.y) <= 0.0 else "B"


def print_competition_summary(
    clusters: list[scan.PumpkinCluster],
) -> list[scan.PumpkinCluster]:
    """Print maturity totals and the required A-N / B-N ripe-fruit line."""
    ripe = v2._ORIGINAL_PRINT_SUMMARY(clusters)
    maturity_counts = Counter(cluster.label() for cluster in clusters)

    a_ripe = sum(zone_for_cluster(cluster) == "A" for cluster in ripe)
    b_ripe = sum(zone_for_cluster(cluster) == "B" for cluster in ripe)

    print("\n========== Pumpkin Count ==========")
    print(f"Orange Pumpkin - {maturity_counts['ORANGE']}")
    print(f"Green Pumpkin - {maturity_counts['GREEN']}")
    if maturity_counts["UNKNOWN"]:
        print(f"Unknown Pumpkin - {maturity_counts['UNKNOWN']}")
    print("===================================")

    print("\n========== 제7회 본선 출력 ==========")
    print(f"A-{a_ripe} / B-{b_ripe}")
    print("======================================")

    if ripe:
        input(
            "로봇팔이 중앙 기본 자세에 있습니다. 주변을 확인한 뒤 "
            "익은 과실 수확을 시작하려면 Enter: "
        )
    return ripe


def main() -> None:
    v4.configure_selective_speed()

    # Use the newly re-taught collision-aware bin poses exactly as saved.
    v2.DROP_RAISE_M = 0.0
    (
        v2._BIN_HOVER_JOINTS,
        v2._BIN_DROP_JOINTS,
        saved_drop_m,
    ) = v2.load_adjusted_bin_poses()

    calibration = scan.base.load_calibrations()
    v2._BIN_FOLDED_JOINTS = np.asarray(
        calibration["camera_joints"], dtype=float
    ).copy()
    v2._BIN_FOLDED_JOINTS[0] = v2._BIN_HOVER_JOINTS[0]

    # Preserve v4's safer release sequence:
    # open -> rise to hover -> restore gripper width -> fold.
    v2.deposit_and_prepare_next = v4.deposit_open_then_rise

    print("새 적재함 자세를 그대로 불러왔습니다:", v2.BIN_POSE_PATH)
    print("적재함 상공 [deg]:", np.round(np.degrees(v2._BIN_HOVER_JOINTS), 1))
    print("적재함 놓기 [deg]:", np.round(np.degrees(v2._BIN_DROP_JOINTS), 1))
    print(f"저장된 상공→놓기 하강량: {saved_drop_m * 1000:.1f} mm")
    print("A 구역: 로봇 기준 +Y / B 구역: 로봇 기준 -Y")
    print("본선 출력 형식: A-[익은 과실 수] / B-[익은 과실 수]")

    scan.require_start = v2.require_full_auto_start
    scan.add_global_track = v2.add_global_track_one_to_one
    scan.print_summary = print_competition_summary
    scan.harvest_one = v2.harvest_one_direct
    scan.AUTO_COUNTDOWN_SEC = 0
    scan.main()


if __name__ == "__main__":
    main()
