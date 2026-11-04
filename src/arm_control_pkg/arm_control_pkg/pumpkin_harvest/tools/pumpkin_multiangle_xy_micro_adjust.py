#!/usr/bin/env python3
"""Measure and save one scan angle's residual XYZ correction safely.

The arm detects one pumpkin at a selected joint1 scan angle, validates the
80/30 mm IK poses without commanding them, then requires a separate
confirmation before moving directly from pre-alignment to the currently
calibrated grasp height.  The operator can jog
in physical XY directions and vertically.  The gripper is never operated.
SAVE stores the resulting XYZ correction for that one angle;
pumpkin_multiangle_approach_validation.py loads it automatically.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from .. import pumpkin_detected_approach_validation as base
from .. import pumpkin_multiangle_approach_validation as multi


DEFAULT_STEP_M = 0.005
SMALL_STEP_M = 0.002
Z_STEP_M = 0.002
MAX_TOTAL_JOG_M = 0.030
MAX_TOTAL_Z_JOG_M = 0.030
CALIBRATION_SPEED_MULTIPLIER = 2.0
ANGLE_MOVE_SPEED_MULTIPLIER = 4.0
READY_DURATION_SEC = 5.0
JOG_DURATION_SEC = 3.0
MAX_JOG_SINGLE_JOINT_DEG = 12.0
MAX_JOG_TOTAL_JOINT_DEG = 30.0
CALIBRATION_OFFSETS_DEG = (-140, -110, -80, -50, 70, 100, 130)
GRID_LABELS = (
    "왼쪽 위", "중앙 위", "오른쪽 위",
    "왼쪽 중앙", "화면 중앙", "오른쪽 중앙",
    "왼쪽 아래", "중앙 아래", "오른쪽 아래",
)


def ask_calibration_offset():
    """Ask for one of the seven angles used by the competition scan."""
    allowed = ", ".join(f"{value:+d}" for value in CALIBRATION_OFFSETS_DEG)
    print("\n보정할 최종 스캔 offset을 입력하세요.")
    print(f"입력 가능: {allowed}")
    while True:
        answer = input("offset [deg] (종료 Q): ").strip()
        if answer.upper() == "Q":
            return None
        try:
            value = int(answer)
        except ValueError:
            print("각도를 정수로 입력하세요.")
            continue
        if value not in CALIBRATION_OFFSETS_DEG:
            print("최종 스캔에 사용하는 7개 각도 중 하나를 입력하세요.")
            continue
        return float(value)


def calibration_duration(normal_duration_sec):
    """Return a tool-local duration without changing harvest timings."""
    duration = float(normal_duration_sec)
    if duration <= 0.0:
        raise ValueError("이동 시간은 0보다 커야 합니다.")
    return duration / CALIBRATION_SPEED_MULTIPLIER


def angle_move_duration(offset_deg):
    """Move between camera angles at 4x the original validated timing."""
    return multi.movement_duration(offset_deg) / ANGLE_MOVE_SPEED_MULTIPLIER


def joint_change(target, seed):
    delta = np.abs(np.degrees(np.asarray(target) - np.asarray(seed)))
    return delta, float(np.max(delta)), float(np.sum(delta))


def solve_pose(arm, xyz, seed, pitch_rad, roll_rad):
    result = multi.inverse_with_wrapped_joint1(
        arm,
        np.asarray(xyz, dtype=float),
        np.asarray(seed, dtype=float),
        float(pitch_rad),
        float(roll_rad),
    )
    if result.shape != np.asarray(seed).shape or not np.all(np.isfinite(result)):
        raise ValueError("미세이동 IK 결과가 올바르지 않습니다.")
    return result


def make_xyz(calibration, world_xy, clearance_m):
    floor_z = base.floor_z_at(
        float(world_xy[0]),
        float(world_xy[1]),
        calibration["floor_coefficients"],
    )
    grasp_z = (
        floor_z
        + calibration["grasp_offset_m"]
        + base.VINE_AVOIDANCE_Z_OFFSET_M
    )
    return np.asarray([world_xy[0], world_xy[1], grasp_z + clearance_m])


def physical_directions(world_xy):
    radial = np.asarray(world_xy, dtype=float)
    length = float(np.linalg.norm(radial))
    if length < 0.050:
        raise ValueError("베이스 방향을 정하기에 목표가 베이스에 너무 가깝습니다.")
    away = radial / length
    left = np.asarray([-away[1], away[0]], dtype=float)
    return {
        "TOWARD_BASE": -away,
        "AWAY_BASE": away,
        "BASE_LEFT": left,
        "BASE_RIGHT": -left,
    }


JOG_COMMAND_ALIASES = {
    "W": "TOWARD_BASE",
    "X": "AWAY_BASE",
    "A": "BASE_LEFT",
    "D": "BASE_RIGHT",
    "R": "Z_UP",
    "F": "Z_DOWN",
    "2": "STEP_2",
    "5": "STEP_5",
    "U": "UNDO",
    "S": "SAVE",
    "Q": "Q",
}


def normalize_jog_command(value):
    command = str(value).strip().upper().replace("-", "_")
    return JOG_COMMAND_ALIASES.get(command, command)


def print_controls(step_m):
    print("\n========== 파지 위치 XYZ 미세조정 ==========")
    print(f"현재 한 번 이동량: {step_m * 1000:.0f} mm")
    print("W / X : 로봇 베이스 쪽 / 베이스에서 멀어지는 쪽")
    print("A / D : 베이스 기준 왼쪽 / 오른쪽")
    print("R / F : 그리퍼 2mm 위 / 아래")
    print("2 / 5 : 한 번 이동량 2mm / 5mm")
    print("U     : 직전 미세이동 취소")
    print("S     : 이 촬영각의 보정값 저장 후 복귀")
    print("Q     : 저장하지 않고 복귀")
    print("그리퍼 동작 없음 / Z 총 추가조정은 위·아래 30mm 이내")
    print("============================================")


def nearer_offsets(commanded_deg):
    """Return safer scan offsets on the same side, ordered toward centre."""
    sign = -1 if commanded_deg < 0 else 1
    candidates = [
        value
        for value in multi.ALLOWED_OFFSETS_DEG
        if abs(value) < abs(commanded_deg)
        and (value == 0 or (value < 0) == (sign < 0))
    ]
    return sorted(candidates, key=lambda value: abs(commanded_deg - value))


def load_store():
    path = multi.ANGLE_RESIDUAL_PATH
    if not path.is_file():
        return {
            "method": "per_angle_manual_world_jog_v1",
            "coordinate_frame": "central_camera_reference_xy",
            "angles": {},
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("method") != "per_angle_manual_world_jog_v1":
        raise ValueError(f"기존 각도별 보정 파일 형식이 다릅니다: {path}")
    if not isinstance(data.get("angles"), dict):
        raise ValueError(f"기존 각도별 보정 angles 형식이 잘못되었습니다: {path}")
    return data


def grid_slot_for_pixel(pixel, image_points):
    """Map a detected pixel to one of nine cells inside the calibration box."""
    points = np.asarray(image_points, dtype=float)
    low = np.min(points, axis=0)
    high = np.max(points, axis=0)
    span = high - low
    if np.any(span <= 0.0):
        raise ValueError("영상 보정 영역의 크기가 올바르지 않습니다.")
    normalized = np.clip((np.asarray(pixel, dtype=float) - low) / span, 0.0, 1.0)
    column = min(2, int(normalized[0] * 3.0))
    row = min(2, int(normalized[1] * 3.0))
    slot = row * 3 + column + 1
    return slot, GRID_LABELS[slot - 1]


def save_residual(
    commanded_deg,
    measured_deg,
    pixel,
    local_residual,
    world_residual,
    grasp_z_residual_m,
    grid_slot,
):
    data = load_store()
    key = str(int(round(commanded_deg)))
    previous = data["angles"].get(key)
    saved_at = datetime.now(timezone.utc).isoformat()
    sample = {
        "grid_slot": int(grid_slot),
        "grid_label": GRID_LABELS[int(grid_slot) - 1],
        "saved_at_utc": saved_at,
        "measured_offset_deg": float(measured_deg),
        "target_pixel_uv": [float(pixel[0]), float(pixel[1])],
        "local_residual_m": [float(v) for v in local_residual],
        "local_residual_mm": [float(v * 1000.0) for v in local_residual],
        "world_residual_m": [float(v) for v in world_residual],
        "world_residual_mm": [float(v * 1000.0) for v in world_residual],
        "grasp_z_residual_m": float(grasp_z_residual_m),
        "grasp_z_residual_mm": float(grasp_z_residual_m * 1000.0),
    }
    samples = [] if not isinstance(previous, dict) else list(
        previous.get("samples", [])
    )
    samples = [
        item for item in samples
        if int(item.get("grid_slot", -1)) != int(grid_slot)
    ]
    samples.append(sample)
    samples.sort(key=lambda item: int(item["grid_slot"]))

    fallback = previous if isinstance(previous, dict) else sample
    record = {
        "saved_at_utc": saved_at,
        "commanded_offset_deg": int(round(commanded_deg)),
        "measured_offset_deg": float(fallback["measured_offset_deg"]),
        "target_pixel_uv": list(fallback["target_pixel_uv"]),
        "local_residual_m": list(fallback["local_residual_m"]),
        "local_residual_mm": list(fallback["local_residual_mm"]),
        "world_residual_m": list(fallback["world_residual_m"]),
        "world_residual_mm": list(fallback["world_residual_mm"]),
        "grasp_z_residual_m": float(fallback["grasp_z_residual_m"]),
        "grasp_z_residual_mm": float(fallback["grasp_z_residual_mm"]),
        "spatial_method": "screen_grid_idw4_v1",
        "sample_count": len(samples),
        "samples": samples,
        "replaces_saved_at_utc": (
            previous.get("saved_at_utc") if isinstance(previous, dict) else None
        ),
    }
    data["angles"][key] = record
    data["updated_at_utc"] = saved_at
    multi.ANGLE_RESIDUAL_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return record


def retreat_to_central(
    arm, calibration, current_xy, current_joints, prealign_joints
):
    seed = np.asarray(current_joints, dtype=float)
    for clearance in (0.050, 0.080):
        xyz = make_xyz(calibration, current_xy, clearance)
        target = solve_pose(
            arm,
            xyz,
            seed,
            calibration["pitch_rad"],
            calibration["roll_rad"],
        )
        _delta, max_delta, total_delta = joint_change(target, seed)
        if max_delta > 25.0 or total_delta > 65.0:
            raise ValueError(
                f"상승 관절 변화가 큽니다: max={max_delta:.1f}, total={total_delta:.1f}도"
            )
        print(f"현재 XY에서 {clearance * 1000:.0f}mm 상공으로 상승합니다.")
        arm.move_joints(
            target,
            duration=calibration_duration(multi.LOWER_MOVE_DURATION_SEC),
        )
        seed = target
    print("80mm 상공에서 수확방향 접힘 자세로 복귀합니다.")
    arm.move_joints(
        prealign_joints,
        duration=calibration_duration(multi.RETURN_DURATION_SEC),
    )
    joint1_delta_deg = np.degrees(
        prealign_joints[0] - calibration["camera_joints"][0]
    )
    print("팔을 접은 상태에서 중앙 안전 자세로 복귀합니다.")
    arm.move_joints(
        calibration["camera_joints"],
        duration=angle_move_duration(joint1_delta_deg),
    )


def legacy_single_sample_main():
    arm = None
    cap = None
    safe_for_automatic_return = False
    at_central_pose = False
    calibration = None
    view_joints = None
    measured_offset_deg = None
    current_xy = None
    current_joints = None

    try:
        calibration = base.load_calibrations()
        existing_residuals = multi.load_angle_residuals()
        saved_z_residuals = multi.load_angle_z_residuals()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 프로그램은 촬영각 하나의 XYZ 잔여오차를 측정합니다.")
        print("그리퍼는 작동하지 않습니다. 확인 후 실제 파지 높이까지 접근합니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        print("촬영각 이동·중앙 복귀 속도: 원래 대비 4.0배")
        print("접근·XYZ 미세조정 속도: 원래 대비 2.0배")
        arm.ready(duration=calibration_duration(READY_DURATION_SEC))

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        arm.move_joints(
            camera_joints,
            duration=calibration_duration(base.CAMERA_MOVE_DURATION_SEC),
        )
        time.sleep(base.SETTLE_TIME_SEC)
        at_central_pose = True

        commanded_offset_deg = ask_calibration_offset()
        if commanded_offset_deg is None:
            raise multi.TestCancelled
        target_joint1_deg = base_joint1_deg + commanded_offset_deg
        if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
            raise ValueError("선택한 촬영 자세가 joint1 안전 한계를 벗어납니다.")
        angle_key = int(round(commanded_offset_deg))
        existing_z_offset = saved_z_residuals.get(
            angle_key,
            multi.DEFAULT_ANGLE_GRASP_Z_OFFSET_M.get(angle_key, 0.0),
        )
        print(
            f"{angle_key:+d}도 기존 Z 보정: "
            f"{existing_z_offset * 1000:+.1f} mm"
        )
        stored_record = load_store()["angles"].get(str(angle_key), {})
        completed_slots = sorted(
            int(item.get("grid_slot"))
            for item in stored_record.get("samples", [])
            if 1 <= int(item.get("grid_slot", -1)) <= 9
        )
        missing_slots = [slot for slot in range(1, 10) if slot not in completed_slots]
        print(f"저장된 9점 칸: {completed_slots or '없음'}")
        print(f"아직 필요한 칸: {missing_slots or '모두 완료'}")

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        print(f"촬영 offset={commanded_offset_deg:+.0f}도로 이동합니다.")
        at_central_pose = False
        arm.move_joints(
            view_joints,
            duration=angle_move_duration(commanded_offset_deg),
        )
        time.sleep(base.SETTLE_TIME_SEC)

        measured = np.asarray(arm.joints(), dtype=float)
        measured_joint1_deg = float(np.degrees(measured[0]))
        measured_offset_deg = measured_joint1_deg - base_joint1_deg
        print(
            f"실측 joint1={measured_joint1_deg:.2f}도 / "
            f"중앙 대비={measured_offset_deg:+.2f}도"
        )

        print("청록색 보정 영역 안에 호박 하나만 놓고 STABLE일 때 M을 누르세요.")
        selected = base.choose_pumpkin(
            model, cap, calibration, show_grid=True
        )
        cap.release()
        cap = None
        cv2.destroyAllWindows()
        if selected is None:
            print("목표 선택을 취소했습니다.")
            arm.move_joints(
                camera_joints,
                duration=angle_move_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        grid_slot, grid_label = grid_slot_for_pixel(
            selected, calibration["image_points"]
        )
        print(
            f"현재 호박 화면 위치: {grid_slot}번 ({grid_label}). "
            "SAVE하면 이 칸의 표본이 저장·교체됩니다."
        )

        try:
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
        except (ValueError, RuntimeError) as error:
            print(f"\n[이동 금지] 베이스 기준 목표 좌표를 만들지 못했습니다: {error}")
            print("중앙 카메라 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=angle_move_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        print(
            "촬영 자세에서 베이스 기준 목표 XY를 확정했습니다: "
            f"x={baseline_world_xy[0]:.4f}, y={baseline_world_xy[1]:.4f} m"
        )
        print("현재 촬영 접힘 자세에서 바로 수확 IK를 계산합니다.")
        start_joints = np.asarray(arm.joints(), dtype=float)
        try:
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
        except (ValueError, RuntimeError) as error:
            print("\n[이동 금지] 현재 목표의 접근 IK를 만들 수 없습니다.")
            print(f"IK 원인: {error}")
            alternatives = nearer_offsets(commanded_offset_deg)[:3]
            if alternatives:
                choices = ", ".join(f"{value:+d}도" for value in alternatives)
                print(f"참고 가능한 중앙 쪽 촬영각: {choices}")
            print("관절 한계를 변경하거나 강제로 이동하지 않습니다.")
            print("중앙 안전 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=angle_move_duration(measured_offset_deg),
            )
            at_central_pose = True
            return
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

        confirmation = input(
            "사람·케이블을 치우고 접힌 채 수확방향으로 돌리려면 PREALIGN 입력: "
        ).strip()
        if confirmation != "PREALIGN":
            print("사전정렬하지 않고 중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=angle_move_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        at_central_pose = False
        arm.move_joints(
            prealign_joints,
            duration=calibration_duration(
                multi.movement_duration(prealign_delta_deg)
            ),
        )
        print("수확방향 사전정렬 완료. 팔은 접힌 자세입니다.")

        print("80mm/30mm 자세는 IK 검증만 완료했으며 실제 이동하지 않습니다.")
        confirmation = input(
            "그리퍼를 작동하지 않고 사전정렬 자세에서 기존 Z가 적용된 "
            "실제 파지 높이로 직접 이동하려면 MOVE_GRASP 입력: "
        ).strip()
        if confirmation != "MOVE_GRASP":
            arm.move_joints(
                camera_joints,
                duration=angle_move_duration(
                    np.degrees(prealign_joints[0] - camera_joints[0])
                ),
            )
            at_central_pose = True
            return
        grasp_xyz = make_xyz(
            calibration, baseline_world_xy, existing_z_offset
        )
        grasp_joints = solve_pose(
            arm,
            grasp_xyz,
            prealign_joints,
            calibration["pitch_rad"],
            calibration["roll_rad"],
        )
        grasp_joints = arm.check_limits(grasp_joints, prealign_joints)
        arm.move_joints(
            grasp_joints,
            duration=calibration_duration(
                multi.HIGH_MOVE_DURATION_SEC + multi.LOWER_MOVE_DURATION_SEC
            ),
        )
        safe_for_automatic_return = True
        current_xy = baseline_world_xy.copy()
        current_z_offset = float(existing_z_offset)
        current_joints = grasp_joints.copy()
        history = []
        step_m = DEFAULT_STEP_M
        print_controls(step_m)

        while True:
            world_jog = current_xy - baseline_world_xy
            total_local = existing_local + multi.rotate_xy(
                world_jog, -measured_offset_deg
            )
            print(
                "현재 이번 실행 이동: "
                f"world dx={world_jog[0] * 1000:+.1f}, "
                f"dy={world_jog[1] * 1000:+.1f} mm | "
                f"저장 예정 local=({total_local[0] * 1000:+.1f}, "
                f"{total_local[1] * 1000:+.1f}) mm, "
                f"Z={current_z_offset * 1000:+.1f} mm"
            )
            command = input("명령: ").strip().upper()

            if command == "STEP_2":
                step_m = SMALL_STEP_M
                print_controls(step_m)
                continue
            if command == "STEP_5":
                step_m = DEFAULT_STEP_M
                print_controls(step_m)
                continue
            if command == "SAVE":
                record = save_residual(
                    commanded_offset_deg,
                    measured_offset_deg,
                    selected,
                    total_local,
                    multi.rotate_xy(total_local, measured_offset_deg),
                    current_z_offset,
                    grid_slot,
                )
                print(
                    f"{commanded_offset_deg:+.0f}도 {grid_slot}번 "
                    f"({grid_label}) 저장: local dx={total_local[0] * 1000:+.1f}, "
                    f"dy={total_local[1] * 1000:+.1f} mm, "
                    f"z={current_z_offset * 1000:+.1f} mm / "
                    f"총 {record['sample_count']}/9점"
                )
                break
            if command == "Q":
                print("저장하지 않고 복귀합니다.")
                break

            if command == "UNDO":
                if not history:
                    print("취소할 미세이동이 없습니다.")
                    continue
                candidate_xy, candidate_z_offset, candidate_joints = history.pop()
            else:
                candidate_xy = current_xy.copy()
                candidate_z_offset = current_z_offset
                if command == "Z_UP":
                    candidate_z_offset += Z_STEP_M
                elif command == "Z_DOWN":
                    candidate_z_offset -= Z_STEP_M
                else:
                    directions = physical_directions(current_xy)
                    direction = directions.get(command)
                    if direction is None:
                        print("표시된 명령 중 하나를 입력하세요.")
                        continue
                    candidate_xy = current_xy + step_m * direction
                if np.linalg.norm(candidate_xy - baseline_world_xy) > MAX_TOTAL_JOG_M + 1e-9:
                    print("[이동 금지] 이번 실행의 총 미세이동은 30mm까지만 허용합니다.")
                    continue
                if abs(candidate_z_offset - existing_z_offset) > MAX_TOTAL_Z_JOG_M + 1e-9:
                    print("[이동 금지] 이번 실행의 Z 추가조정은 30mm까지만 허용합니다.")
                    continue

                candidate_reference = multi.rotate_xy(
                    candidate_xy, -measured_offset_deg
                )
                inside, margin = base.inside_hull(
                    candidate_reference, calibration["robot_points"]
                )
                if not inside:
                    print(
                        "[이동 금지] 후보점이 9점 보정 영역 밖입니다: "
                        f"{margin * 1000:.1f} mm"
                    )
                    continue

                candidate_xyz = make_xyz(
                    calibration, candidate_xy, candidate_z_offset
                )
                try:
                    candidate_joints = solve_pose(
                        arm,
                        candidate_xyz,
                        current_joints,
                        calibration["pitch_rad"],
                        calibration["roll_rad"],
                    )
                except (ValueError, RuntimeError) as error:
                    print(f"[이동 금지] 미세이동 IK 실패: {error}")
                    continue
                _delta, max_delta, total_delta = joint_change(
                    candidate_joints, current_joints
                )
                if max_delta > MAX_JOG_SINGLE_JOINT_DEG or total_delta > MAX_JOG_TOTAL_JOINT_DEG:
                    print(
                        "[이동 금지] 관절 변화량이 큽니다: "
                        f"max={max_delta:.1f}, total={total_delta:.1f}도"
                    )
                    continue
                history.append((
                    current_xy.copy(), current_z_offset, current_joints.copy()
                ))

            print(
                f"{command}: 목표 XYZ=({candidate_xy[0]:.4f}, "
                f"{candidate_xy[1]:.4f}, Z보정 "
                f"{candidate_z_offset * 1000:+.1f}mm)"
            )
            safe_for_automatic_return = False
            arm.move_joints(
                candidate_joints,
                duration=calibration_duration(JOG_DURATION_SEC),
            )
            current_xy = candidate_xy
            current_z_offset = candidate_z_offset
            current_joints = candidate_joints
            safe_for_automatic_return = True

        safe_for_automatic_return = False
        retreat_to_central(
            arm,
            calibration,
            current_xy,
            current_joints,
            prealign_joints,
        )
        safe_for_automatic_return = True
        at_central_pose = True
        print(f"결과 파일: {multi.ANGLE_RESIDUAL_PATH}")

    except multi.TestCancelled:
        print("미세조정을 취소했습니다.")
    except KeyboardInterrupt:
        safe_for_automatic_return = False
        at_central_pose = False
        print("\n사용자가 중단했습니다. 자동 이동을 생략합니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        if arm is not None:
            try:
                if safe_for_automatic_return and not at_central_pose and current_xy is not None:
                    try:
                        retreat_to_central(
                            arm,
                            calibration,
                            current_xy,
                            np.asarray(arm.joints(), dtype=float),
                            prealign_joints,
                        )
                        at_central_pose = True
                    except (ValueError, RuntimeError) as error:
                        safe_for_automatic_return = False
                        print(f"자동 안전 복귀 실패: {error}")
                if at_central_pose:
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print("자동 정리 자세를 생략합니다. 로봇이 멈췄는지 확인하세요.")
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")


def main():
    from . import pumpkin_multiangle_xyz_grid_adjust

    return pumpkin_multiangle_xyz_grid_adjust.main()


if __name__ == "__main__":
    main()
