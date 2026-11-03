#!/usr/bin/env python3
"""Calibrate all nine screen-position XYZ samples at one scan angle."""

from __future__ import annotations

import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from .. import pumpkin_detected_approach_validation as base
from .. import pumpkin_multiangle_approach_validation as multi
from . import pumpkin_multiangle_xy_micro_adjust as common


def completed_slots(angle: int) -> list[int]:
    record = common.load_store()["angles"].get(str(angle), {})
    slots = set()
    for item in record.get("samples", []):
        try:
            slot = int(item.get("grid_slot"))
        except (TypeError, ValueError):
            continue
        if 1 <= slot <= 9:
            slots.add(slot)
    return sorted(slots)


def return_to_same_view(
    arm, calibration, current_xy, current_joints, prealign_joints, view_joints
):
    """Rise from the sample and return to the same angle, not the centre."""
    seed = np.asarray(current_joints, dtype=float)
    for clearance in (0.050, 0.080):
        target = common.solve_pose(
            arm,
            common.make_xyz(calibration, current_xy, clearance),
            seed,
            calibration["pitch_rad"],
            calibration["roll_rad"],
        )
        arm.move_joints(
            target,
            duration=common.calibration_duration(multi.LOWER_MOVE_DURATION_SEC),
        )
        seed = target
    arm.move_joints(
        prealign_joints,
        duration=common.calibration_duration(multi.RETURN_DURATION_SEC),
    )
    delta_deg = np.degrees(prealign_joints[0] - view_joints[0])
    arm.move_joints(
        view_joints,
        duration=common.angle_move_duration(delta_deg),
    )


def select_one(model, calibration):
    cap = base.open_camera()
    try:
        print("자주색 격자의 아직 저장하지 않은 칸에 호박 하나를 놓으세요.")
        return base.choose_pumpkin(
            model, cap, calibration, show_grid=True
        )
    finally:
        cap.release()
        cv2.destroyAllWindows()


def calibrate_one_sample(
    arm,
    model,
    calibration,
    existing_residuals,
    commanded_offset_deg,
    measured_offset_deg,
    view_joints,
):
    """Calibrate one grid cell and return (saved, stop_session)."""
    selected = select_one(model, calibration)
    if selected is None:
        return False, True
    grid_slot, grid_label = common.grid_slot_for_pixel(
        selected, calibration["image_points"]
    )
    print(f"선택 위치: {grid_slot}번 ({grid_label})")

    target = multi.build_rotated_target(
        calibration,
        selected,
        commanded_offset_deg,
        measured_offset_deg,
        existing_residuals,
    )
    baseline_world_xy = target["world_target_xy"].copy()
    existing_local = target["residual_local"].copy()
    existing_z_offset = float(target["resolved_grasp_z_residual_m"])
    start_joints = np.asarray(arm.joints(), dtype=float)
    (
        prealign_joints,
        prealign_delta_deg,
        joints_stages,
        deltas,
    ) = multi.plan_fixed_pose_stages_from_folded_pose(
        arm,
        target["xyz_stages"],
        start_joints,
        calibration["pitch_rad"],
        calibration["roll_rad"],
    )
    multi.print_plan(
        target,
        commanded_offset_deg,
        measured_offset_deg,
        calibration,
        start_joints,
        prealign_joints,
        prealign_delta_deg,
        joints_stages,
        deltas,
    )
    print("호박 위치 확정 후 수확방향 사전정렬 자세로 자동 이동합니다.")
    arm.move_joints(
        prealign_joints,
        duration=common.calibration_duration(
            multi.movement_duration(prealign_delta_deg)
        ),
    )
    print("80mm/30mm 자세는 IK 검증만 하고 실제 이동하지 않습니다.")
    if input(
        "기존 Z 파지 높이로 직접 이동하려면 MOVE_GRASP 입력: "
    ).strip() != "MOVE_GRASP":
        arm.move_joints(
            view_joints,
            duration=common.angle_move_duration(
                np.degrees(prealign_joints[0] - view_joints[0])
            ),
        )
        return False, True

    grasp_joints = common.solve_pose(
        arm,
        common.make_xyz(calibration, baseline_world_xy, existing_z_offset),
        prealign_joints,
        calibration["pitch_rad"],
        calibration["roll_rad"],
    )
    grasp_joints = arm.check_limits(grasp_joints, prealign_joints)
    arm.move_joints(
        grasp_joints,
        duration=common.calibration_duration(
            multi.HIGH_MOVE_DURATION_SEC + multi.LOWER_MOVE_DURATION_SEC
        ),
    )

    current_xy = baseline_world_xy.copy()
    current_z_offset = existing_z_offset
    current_joints = grasp_joints.copy()
    history = []
    step_m = common.DEFAULT_STEP_M
    common.print_controls(step_m)
    saved = False
    stop_session = False
    while True:
        world_jog = current_xy - baseline_world_xy
        total_local = existing_local + multi.rotate_xy(
            world_jog, -measured_offset_deg
        )
        print(
            f"저장 예정: local XY=({total_local[0] * 1000:+.1f}, "
            f"{total_local[1] * 1000:+.1f})mm, "
            f"Z={current_z_offset * 1000:+.1f}mm"
        )
        command = input("명령: ").strip().upper()
        if command == "STEP_2":
            step_m = common.SMALL_STEP_M
            common.print_controls(step_m)
            continue
        if command == "STEP_5":
            step_m = common.DEFAULT_STEP_M
            common.print_controls(step_m)
            continue
        if command == "SAVE":
            record = common.save_residual(
                commanded_offset_deg,
                measured_offset_deg,
                selected,
                total_local,
                multi.rotate_xy(total_local, measured_offset_deg),
                current_z_offset,
                grid_slot,
            )
            print(
                f"{grid_slot}번 ({grid_label}) 저장 완료: "
                f"총 {record['sample_count']}/9점"
            )
            saved = True
            break
        if command == "Q":
            stop_session = True
            break

        if command == "UNDO":
            if not history:
                print("취소할 미세이동이 없습니다.")
                continue
            current_xy, current_z_offset, current_joints = history.pop()
            arm.move_joints(
                current_joints,
                duration=common.calibration_duration(common.JOG_DURATION_SEC),
            )
            continue

        candidate_xy = current_xy.copy()
        candidate_z = current_z_offset
        if command == "Z_UP":
            candidate_z += common.Z_STEP_M
        elif command == "Z_DOWN":
            candidate_z -= common.Z_STEP_M
        else:
            direction = common.physical_directions(current_xy).get(command)
            if direction is None:
                print("표시된 명령 중 하나를 입력하세요.")
                continue
            candidate_xy += step_m * direction
        if np.linalg.norm(candidate_xy - baseline_world_xy) > common.MAX_TOTAL_JOG_M:
            print("[이동 금지] XY 추가조정은 30mm까지만 허용합니다.")
            continue
        if abs(candidate_z - existing_z_offset) > common.MAX_TOTAL_Z_JOG_M:
            print("[이동 금지] Z 추가조정은 30mm까지만 허용합니다.")
            continue
        reference_xy = multi.rotate_xy(candidate_xy, -measured_offset_deg)
        inside, _margin = base.inside_hull(
            reference_xy, calibration["robot_points"]
        )
        if not inside:
            print("[이동 금지] 후보점이 9점 로봇 보정 영역 밖입니다.")
            continue
        candidate_joints = common.solve_pose(
            arm,
            common.make_xyz(calibration, candidate_xy, candidate_z),
            current_joints,
            calibration["pitch_rad"],
            calibration["roll_rad"],
        )
        _delta, max_delta, total_delta = common.joint_change(
            candidate_joints, current_joints
        )
        if (
            max_delta > common.MAX_JOG_SINGLE_JOINT_DEG
            or total_delta > common.MAX_JOG_TOTAL_JOINT_DEG
        ):
            print("[이동 금지] 미세이동 관절 변화량이 큽니다.")
            continue
        history.append((current_xy.copy(), current_z_offset, current_joints.copy()))
        arm.move_joints(
            candidate_joints,
            duration=common.calibration_duration(common.JOG_DURATION_SEC),
        )
        current_xy = candidate_xy
        current_z_offset = candidate_z
        current_joints = candidate_joints

    return_to_same_view(
        arm,
        calibration,
        current_xy,
        current_joints,
        prealign_joints,
        view_joints,
    )
    return saved, stop_session


def main():
    arm = None
    at_central = False
    at_view = False
    calibration = None
    camera_joints = None
    view_joints = None
    try:
        calibration = base.load_calibrations()
        existing_residuals = multi.load_angle_residuals()
        model = YOLO(str(base.find_model_path()))
        base.validate_model(model)
        angle = common.ask_calibration_offset()
        if angle is None:
            return
        angle_key = int(round(angle))

        arm = OmxFollower().connect()
        arm.ready(duration=common.calibration_duration(common.READY_DURATION_SEC))
        camera_joints = calibration["camera_joints"]
        arm.move_joints(
            camera_joints,
            duration=common.calibration_duration(base.CAMERA_MOVE_DURATION_SEC),
        )
        time.sleep(base.SETTLE_TIME_SEC)
        at_central = True
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        target_joint1_deg = base_joint1_deg + angle
        if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
            raise ValueError("선택 각도가 joint1 안전 한계를 벗어납니다.")
        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        arm.move_joints(view_joints, duration=common.angle_move_duration(angle))
        time.sleep(base.SETTLE_TIME_SEC)
        at_central = False
        at_view = True
        measured = np.asarray(arm.joints(), dtype=float)
        measured_offset = float(np.degrees(measured[0])) - base_joint1_deg

        while True:
            done = completed_slots(angle_key)
            missing = [slot for slot in range(1, 10) if slot not in done]
            print(f"\n{angle_key:+d}도 저장 완료: {done or '없음'}")
            print(f"남은 칸: {missing or '없음'}")
            if not missing:
                print("이 각도의 9점 XYZ 보정이 모두 완료됐습니다.")
                break
            # From here until the helper returns, do not assume a safe pose;
            # an exception during direct approach must not trigger an
            # automatic centre sweep from an unknown arm configuration.
            at_view = False
            saved, stop = calibrate_one_sample(
                arm,
                model,
                calibration,
                existing_residuals,
                angle,
                measured_offset,
                view_joints,
            )
            at_view = True
            if stop:
                break
            if not saved:
                print("표본을 저장하지 않았습니다.")

        arm.move_joints(
            camera_joints,
            duration=common.angle_move_duration(measured_offset),
        )
        at_view = False
        at_central = True
        print("9점 보정 세션을 마치고 중앙 자세로 복귀했습니다.")
    except KeyboardInterrupt:
        at_view = False
        at_central = False
        print("\n사용자가 중단했습니다. 자동 이동을 생략합니다.")
    finally:
        cv2.destroyAllWindows()
        if arm is not None:
            try:
                if at_view and camera_joints is not None:
                    arm.move_joints(
                        camera_joints,
                        duration=common.angle_move_duration(
                            np.degrees(view_joints[0] - camera_joints[0])
                        ),
                    )
                    at_central = True
                if at_central:
                    arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
