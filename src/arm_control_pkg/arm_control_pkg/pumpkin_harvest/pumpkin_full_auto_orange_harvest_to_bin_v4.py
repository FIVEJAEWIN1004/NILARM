#!/usr/bin/env python3
"""Full-auto orange harvest v4 with selective arm speeds.

The newly re-taught bin poses are used exactly as saved.  Preparation and
normal arm transit run 1.5x faster than the v3 speed.  Scan rotations run
another 1.3x faster, while motions carrying a grasped pumpkin run another 2x
faster than their current setting.  Pumpkin and bin descents retain the v3
speed.  Gripper timing is unchanged.  After release, the open gripper rises to
bin hover before its width is restored.
"""

from __future__ import annotations

import time

import numpy as np

from . import pumpkin_auto_scan_count_orange_harvest as scan
from . import pumpkin_full_auto_orange_harvest_to_bin_v2 as v2


# v3 used 0.90 of the original duration.  Dividing that duration by 1.5 gives
# 0.60 of the original duration for all non-descent arm motions.
TRANSIT_DURATION_FACTOR = 0.60
SCAN_EXTRA_SPEED_MULTIPLIER = 1.30
FIRST_SCAN_ENTRY_SPEED_MULTIPLIER = 2.0
SCAN_ROTATION_DURATION_FACTOR = (
    TRANSIT_DURATION_FACTOR / SCAN_EXTRA_SPEED_MULTIPLIER
)
DESCENT_DURATION_FACTOR = 0.90
MIN_ROTATION_DURATION_SEC = 2.0

BIN_HOVER_DURATION_SEC = (
    8.0
    * TRANSIT_DURATION_FACTOR
    / v2.HELD_TRANSPORT_SPEED_MULTIPLIER
)
BIN_DESCENT_DURATION_SEC = 3.0 * DESCENT_DURATION_FACTOR
BIN_ASCENT_DURATION_SEC = 3.0 * TRANSIT_DURATION_FACTOR
BIN_FOLD_DURATION_SEC = 8.0 * TRANSIT_DURATION_FACTOR
BIN_SETTLE_SEC = 0.7

_ORIGINAL_MOVEMENT_DURATION = scan.multi.movement_duration


def wait_for_manual_departure_signal() -> None:
    """Temporary manual gate at the future mobile-departure signal point."""
    input(
        "\n[주행 출발 준비] 마지막 호박 적재와 그리퍼 상승이 완료됐습니다. "
        "주행 출발 신호 시점을 확인하려면 Enter: "
    )
    print("[주행 출발 신호] Enter 확인 완료. 로봇팔 정리를 계속합니다.")


# Replace this callable with ROS signaling when automatic Pinky departure is
# enabled.  Keeping one hook makes the later change independent of arm motion.
departure_signal_gate = wait_for_manual_departure_signal


def transit_rotation_duration(delta_deg: float) -> float:
    return max(
        MIN_ROTATION_DURATION_SEC,
        float(_ORIGINAL_MOVEMENT_DURATION(delta_deg))
        * TRANSIT_DURATION_FACTOR,
    )


def scan_rotation_duration(delta_deg: float) -> float:
    """Run scan rotations 1.3x faster than the existing transit speed."""
    return max(
        MIN_ROTATION_DURATION_SEC,
        float(_ORIGINAL_MOVEMENT_DURATION(delta_deg))
        * SCAN_ROTATION_DURATION_FACTOR,
    )


def scan_target_rotation_duration(
    commanded_deg: float,
    delta_deg: float,
) -> float:
    """Double only the move into the first -140-degree scan view."""
    duration = scan_rotation_duration(delta_deg)
    if int(round(float(commanded_deg))) == -140:
        return duration / FIRST_SCAN_ENTRY_SPEED_MULTIPLIER
    return duration


def configure_selective_speed() -> None:
    """Speed up non-descent arm motions; preserve descents and gripper."""
    scan.base.CAMERA_MOVE_DURATION_SEC *= TRANSIT_DURATION_FACTOR

    # 80 mm high approach is a free-space transit motion.
    scan.grasp.HIGH_MOVE_DURATION_SEC *= TRANSIT_DURATION_FACTOR

    # 80 -> 30 -> 10 -> 0 mm pumpkin descent keeps the v3 speed.
    scan.grasp.LOWER_MOVE_DURATION_SEC *= DESCENT_DURATION_FACTOR

    # Base free-space speed; v2 applies the additional held-load 2x factor
    # only after the gripper has closed.
    scan.grasp.LIFT_STEP_DURATION_SEC *= TRANSIT_DURATION_FACTOR
    scan.grasp.RETURN_DURATION_SEC *= TRANSIT_DURATION_FACTOR

    # Keep preparation and folded transport at the existing 1.5x speed.
    scan.multi.movement_duration = transit_rotation_duration

    # Only the automatic scan sweep is another 1.3x faster.
    scan.scan_movement_duration = scan_rotation_duration
    scan.scan_target_movement_duration = scan_target_rotation_duration


def deposit_open_then_rise(
    arm,
    calibration,
    default_gripper_value: float,
    is_last: bool,
) -> None:
    if (
        v2._BIN_HOVER_JOINTS is None
        or v2._BIN_DROP_JOINTS is None
        or v2._BIN_FOLDED_JOINTS is None
    ):
        raise RuntimeError("새 적재함 자세가 준비되지 않았습니다.")

    v2.validate_bin_limits(
        arm,
        ("적재함 상공", v2._BIN_HOVER_JOINTS),
        ("적재함 놓기", v2._BIN_DROP_JOINTS),
        ("적재함 방향 접힘", v2._BIN_FOLDED_JOINTS),
    )

    print("[적재] 호박을 든 채 적재함 상공으로 이동합니다. (현재보다 2배)")
    arm.move_joints(
        v2._BIN_HOVER_JOINTS,
        duration=BIN_HOVER_DURATION_SEC,
    )
    time.sleep(BIN_SETTLE_SEC)

    print("[적재] 새로 저장한 놓기 자세로 하강합니다. (현재 속도 유지)")
    arm.move_joints(
        v2._BIN_DROP_JOINTS,
        duration=BIN_DESCENT_DURATION_SEC,
    )
    time.sleep(BIN_SETTLE_SEC)

    print("[적재] 그리퍼를 열어 주황 호박을 놓습니다.")
    arm.open_gripper(
        duration=scan.grasp.GRIPPER_OPEN_DURATION_SEC,
        stall_guard=True,
        wait=True,
    )
    time.sleep(BIN_SETTLE_SEC)

    # Keep the gripper open until it has cleared the robot/bin obstacles.
    print("[적재] 열린 그리퍼 그대로 적재함 상공 자세로 먼저 복귀합니다. (1.5배)")
    arm.move_joints(
        v2._BIN_HOVER_JOINTS,
        duration=BIN_ASCENT_DURATION_SEC,
    )
    time.sleep(BIN_SETTLE_SEC)

    if is_last:
        departure_signal_gate()

    print("[적재] 상공에서 시작 당시 기본 그리퍼 폭으로 정리합니다.")
    arm.gripper(
        default_gripper_value,
        duration=scan.RESTORE_GRIPPER_DURATION_SEC,
        stall_guard=False,
        wait=True,
    )

    print("[다음 목표 준비] 적재함 방향에서 팔을 접습니다. (1.5배)")
    arm.move_joints(
        v2._BIN_FOLDED_JOINTS,
        duration=BIN_FOLD_DURATION_SEC,
    )

    if is_last:
        rotation_deg = float(
            np.degrees(
                calibration["camera_joints"][0]
                - v2._BIN_FOLDED_JOINTS[0]
            )
        )
        print("[수확 완료] 마지막 과실이므로 중앙 안전 자세로 복귀합니다. (1.5배)")
        arm.move_joints(
            calibration["camera_joints"],
            duration=transit_rotation_duration(rotation_deg),
        )
        time.sleep(scan.base.SETTLE_TIME_SEC)
    else:
        print("[다음 목표 준비] 중앙 자세를 거치지 않고 다음 과실로 진행합니다.")


def main() -> None:
    configure_selective_speed()

    # The collision-aware poses were just re-taught.  Use the saved drop pose
    # exactly, without the older v2/v3 additional height interpolation.
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

    # v2's harvest action looks up the deposit function from its module at
    # runtime, so replace only that stage with the safer ordering above.
    v2.deposit_and_prepare_next = deposit_open_then_rise

    print("새 적재함 자세를 그대로 불러왔습니다:", v2.BIN_POSE_PATH)
    print("적재함 상공 [deg]:", np.round(np.degrees(v2._BIN_HOVER_JOINTS), 1))
    print("적재함 놓기 [deg]:", np.round(np.degrees(v2._BIN_DROP_JOINTS), 1))
    print(f"저장된 상공→놓기 하강량: {saved_drop_m * 1000:.1f} mm")
    print("일반 준비·이동: v3보다 1.5배")
    print("호박을 잡은 뒤 상승·접기·적재함 이동: 현재 설정보다 2배")
    print("호박 집기 하강·적재함 하강·그리퍼: v3 속도 유지")
    print("호박 배출 후 열린 그리퍼로 상공 복귀한 다음 그리퍼를 정리합니다.")

    scan.require_start = v2.require_full_auto_start
    scan.add_global_track = v2.add_global_track_one_to_one
    scan.print_summary = v2.print_summary_with_requested_names
    scan.harvest_one = v2.harvest_one_direct
    scan.AUTO_COUNTDOWN_SEC = 0
    scan.main()


if __name__ == "__main__":
    main()
