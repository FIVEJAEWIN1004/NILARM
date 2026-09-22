#!/usr/bin/env python3
"""Measure and save one scan angle's residual XY correction safely.

The arm detects one pumpkin at a selected joint1 scan angle, approaches only
to 30 mm above the planned grasp pose, and lets the operator jog in physical
directions (toward/away from the base and base-view left/right).  The gripper
is never operated.  SAVE stores the resulting correction for that one angle;
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
import pumpkin_detected_approach_validation as base
import pumpkin_multiangle_approach_validation as multi


DEFAULT_STEP_M = 0.005
SMALL_STEP_M = 0.002
MAX_TOTAL_JOG_M = 0.030
JOG_DURATION_SEC = 3.0
MAX_JOG_SINGLE_JOINT_DEG = 12.0
MAX_JOG_TOTAL_JOINT_DEG = 30.0


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


def print_controls(step_m):
    print("\n========== 30mm 상공 XY 미세조정 ==========")
    print(f"현재 한 번 이동량: {step_m * 1000:.0f} mm")
    print("TOWARD_BASE : 로봇 베이스 쪽")
    print("AWAY_BASE   : 로봇 베이스에서 멀어지는 쪽")
    print("BASE_LEFT   : 베이스에서 그리퍼를 볼 때 왼쪽")
    print("BASE_RIGHT  : 베이스에서 그리퍼를 볼 때 오른쪽")
    print("STEP_2 / STEP_5 : 한 번 이동량 2mm / 5mm")
    print("UNDO        : 직전 미세이동 취소")
    print("SAVE        : 이 촬영각의 보정값 저장 후 복귀")
    print("Q           : 저장하지 않고 복귀")
    print("그리퍼 동작 없음 / 30mm 아래로 내려가지 않음")
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


def save_residual(commanded_deg, measured_deg, pixel, local_residual, world_residual):
    data = load_store()
    key = str(int(round(commanded_deg)))
    previous = data["angles"].get(key)
    record = {
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "commanded_offset_deg": int(round(commanded_deg)),
        "measured_offset_deg": float(measured_deg),
        "target_pixel_uv": [float(pixel[0]), float(pixel[1])],
        "local_residual_m": [float(v) for v in local_residual],
        "local_residual_mm": [float(v * 1000.0) for v in local_residual],
        "world_residual_m": [float(v) for v in world_residual],
        "world_residual_mm": [float(v * 1000.0) for v in world_residual],
        "replaces_saved_at_utc": (
            previous.get("saved_at_utc") if isinstance(previous, dict) else None
        ),
    }
    data["angles"][key] = record
    data["updated_at_utc"] = record["saved_at_utc"]
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
        arm.move_joints(target, duration=multi.LOWER_MOVE_DURATION_SEC)
        seed = target
    print("80mm 상공에서 수확방향 접힘 자세로 복귀합니다.")
    arm.move_joints(prealign_joints, duration=multi.RETURN_DURATION_SEC)
    joint1_delta_deg = np.degrees(
        prealign_joints[0] - calibration["camera_joints"][0]
    )
    print("팔을 접은 상태에서 중앙 안전 자세로 복귀합니다.")
    arm.move_joints(
        calibration["camera_joints"],
        duration=multi.movement_duration(joint1_delta_deg),
    )


def main():
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
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 프로그램은 촬영각 하나의 XY 잔여오차를 측정합니다.")
        print("그리퍼는 작동하지 않으며 30mm 상공까지만 접근합니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        arm.move_joints(camera_joints, duration=base.CAMERA_MOVE_DURATION_SEC)
        time.sleep(base.SETTLE_TIME_SEC)
        at_central_pose = True

        commanded_offset_deg = multi.ask_offset()
        if commanded_offset_deg is None:
            raise multi.TestCancelled
        target_joint1_deg = base_joint1_deg + commanded_offset_deg
        if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
            raise ValueError("선택한 촬영 자세가 joint1 안전 한계를 벗어납니다.")

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        print(f"촬영 offset={commanded_offset_deg:+.0f}도로 이동합니다.")
        at_central_pose = False
        arm.move_joints(
            view_joints,
            duration=multi.movement_duration(commanded_offset_deg),
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
        selected = base.choose_pumpkin(model, cap, calibration)
        cap.release()
        cap = None
        cv2.destroyAllWindows()
        if selected is None:
            print("목표 선택을 취소했습니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

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
        except (ValueError, RuntimeError) as error:
            print(f"\n[이동 금지] 베이스 기준 목표 좌표를 만들지 못했습니다: {error}")
            print("중앙 카메라 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(measured_offset_deg),
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
                duration=multi.movement_duration(measured_offset_deg),
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
                duration=multi.movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        at_central_pose = False
        arm.move_joints(
            prealign_joints,
            duration=multi.movement_duration(prealign_delta_deg),
        )
        print("수확방향 사전정렬 완료. 팔은 접힌 자세입니다.")

        confirmation = input(
            "주변이 안전하면 80mm 상공으로 이동하려면 MOVE_HIGH 입력: "
        ).strip()
        if confirmation != "MOVE_HIGH":
            print("80mm 상공으로 이동하지 않고 중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(
                    np.degrees(prealign_joints[0] - camera_joints[0])
                ),
            )
            at_central_pose = True
            return
        arm.move_joints(joints_stages[0], duration=multi.HIGH_MOVE_DURATION_SEC)

        confirmation = input(
            "정렬·주변이 안전하면 30mm 상공으로 바로 낮추려면 MOVE_30 입력: "
        ).strip()
        if confirmation != "MOVE_30":
            multi.return_from_stage_to_central(
                arm, calibration, prealign_joints, joints_stages, 0
            )
            at_central_pose = True
            return
        arm.move_joints(joints_stages[1], duration=multi.LOWER_MOVE_DURATION_SEC)
        safe_for_automatic_return = True
        current_xy = baseline_world_xy.copy()
        current_joints = joints_stages[1].copy()
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
                f"{total_local[1] * 1000:+.1f}) mm"
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
                )
                print(
                    f"{commanded_offset_deg:+.0f}도 보정 저장: "
                    f"local dx={record['local_residual_mm'][0]:+.1f}, "
                    f"dy={record['local_residual_mm'][1]:+.1f} mm"
                )
                break
            if command == "Q":
                print("저장하지 않고 복귀합니다.")
                break

            if command == "UNDO":
                if not history:
                    print("취소할 미세이동이 없습니다.")
                    continue
                candidate_xy, candidate_joints = history.pop()
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

                candidate_xyz = make_xyz(calibration, candidate_xy, 0.030)
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
                history.append((current_xy.copy(), current_joints.copy()))

            print(
                f"{command}: 목표 XY=({candidate_xy[0]:.4f}, "
                f"{candidate_xy[1]:.4f}) m"
            )
            safe_for_automatic_return = False
            arm.move_joints(candidate_joints, duration=JOG_DURATION_SEC)
            current_xy = candidate_xy
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


if __name__ == "__main__":
    main()
