#!/usr/bin/env python3
"""Validate pumpkin XY approach from a selected joint1 camera angle.

One run validates one scan offset.  The central 9-point homography converts a
YOLO box centre into reference-frame XY.  The verified +10 mm local-forward
correction is applied in that reference frame, then both the target and the
correction are rotated by the measured joint1 offset into the OMX base frame.

After detection, the target is frozen in the fixed robot-base frame.  IK is
planned immediately from the already-folded scan pose; the arm only adjusts
joint1 to the harvest direction before approaching 80 mm and then moving
directly to 30 mm above the planned grasp pose.  It never operates the gripper
or reaches grasp height.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from . import pumpkin_detected_approach_validation as base


ALLOWED_OFFSETS_DEG = (-140, -110, -80, -50, -20, 0, 10, 40, 70, 100, 130, 140)
RECOMMENDED_VALIDATION_OFFSETS_DEG = (-140, -80, 70, 140)
JOINT1_SAFE_LIMIT_DEG = 145.0

# Positive OMX joint1 is treated as positive XY rotation.  The purpose of
# testing both negative and positive offsets is to validate this convention.
JOINT1_ROTATION_SIGN = 1.0

# Angle-specific residuals are written only by
# pumpkin_multiangle_xy_micro_adjust.py.  The previously guessed -80 degree
# correction was intentionally removed; a missing/invalid angle is zero.
ANGLE_RESIDUAL_PATH = Path(__file__).with_name(
    "pumpkin_multiangle_xy_residual.json"
)

APPROACH_CLEARANCES_M = (0.080, 0.030)
HIGH_MOVE_DURATION_SEC = 12.0
LOWER_MOVE_DURATION_SEC = 8.0
RETURN_DURATION_SEC = 12.0
SCAN_STEP_DURATION_SEC = 6.0


class TestCancelled(Exception):
    """Raised when the user cancels before target motion."""


def load_angle_residuals(path: Path | None = None) -> dict[int, np.ndarray]:
    """Load manually verified local XY residuals keyed by commanded angle."""
    if path is None:
        path = ANGLE_RESIDUAL_PATH
    if not path.is_file():
        print("각도별 XY 보정 파일이 없어 추가 잔여보정 없이 실행합니다.")
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("method") != "per_angle_manual_world_jog_v1":
        raise ValueError(f"각도별 XY 보정 파일 형식이 다릅니다: {path}")
    angles = data.get("angles")
    if not isinstance(angles, dict):
        raise ValueError(f"각도별 XY 보정 angles 형식이 잘못되었습니다: {path}")

    residuals: dict[int, np.ndarray] = {}
    for key, record in angles.items():
        try:
            angle = int(key)
        except (TypeError, ValueError) as error:
            raise ValueError(f"잘못된 촬영각 키입니다: {key!r}") from error
        if angle not in ALLOWED_OFFSETS_DEG or not isinstance(record, dict):
            raise ValueError(f"허용되지 않은 촬영각 보정입니다: {key!r}")
        value = np.asarray(record.get("local_residual_m"), dtype=float)
        if value.shape != (2,) or not np.all(np.isfinite(value)):
            raise ValueError(f"{angle:+d}도 local_residual_m 형식이 잘못되었습니다.")
        if np.linalg.norm(value) > 0.050:
            raise ValueError(f"{angle:+d}도 잔여보정이 50 mm를 초과합니다.")
        residuals[angle] = value
    print(f"각도별 XY 보정 {len(residuals)}개를 불러왔습니다: {path}")
    return residuals


def movement_duration(delta_deg: float) -> float:
    """Move large joint1 rotations no faster than a normal 30-degree step."""
    return max(
        SCAN_STEP_DURATION_SEC,
        abs(float(delta_deg)) / 30.0 * SCAN_STEP_DURATION_SEC,
    )


def ask_offset() -> float | None:
    allowed = ", ".join(f"{value:+d}" for value in ALLOWED_OFFSETS_DEG)
    recommended = ", ".join(
        f"{value:+d}" for value in RECOMMENDED_VALIDATION_OFFSETS_DEG
    )
    while True:
        text = input(
            "\n검증할 촬영 offset을 입력하세요.\n"
            f"권장 검증 순서: {recommended}\n"
            f"입력 가능: {allowed}\n"
            "offset [deg] (종료 Q): "
        ).strip()
        if text.upper() == "Q":
            return None
        try:
            value = int(text)
        except ValueError:
            print("목록에 있는 정수 각도를 입력하세요.")
            continue
        if value not in ALLOWED_OFFSETS_DEG:
            print("입력 가능한 촬영각 목록에서 선택하세요.")
            continue
        return float(value)


def rotate_xy(point_xy, offset_deg: float) -> np.ndarray:
    angle = math.radians(offset_deg * JOINT1_ROTATION_SIGN)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    rotation = np.asarray(
        [[cosine, -sine], [sine, cosine]], dtype=float
    )
    result = rotation @ np.asarray(point_xy, dtype=float)
    if result.shape != (2,) or not np.all(np.isfinite(result)):
        raise ValueError("촬영각 회전 좌표가 올바르지 않습니다.")
    return result


def wrap_to_pi(angle_rad: float) -> float:
    """Return an equivalent revolute-joint angle in [-pi, pi]."""
    return math.atan2(math.sin(float(angle_rad)), math.cos(float(angle_rad)))


def inverse_with_wrapped_joint1(
    arm, xyz, seed, pitch_rad: float, roll_rad: float
) -> np.ndarray:
    """Run normal IK, then safely recover the known analytic joint1 wrap bug.

    omx_f analytic IK can return e.g. +243 degrees for a physically equivalent
    -117 degree joint1 pose.  Its limit check happens before normalization.
    This fallback changes only joint1 by whole turns, then rechecks every joint
    limit and verifies the result with forward kinematics.
    """
    kinematics = base.get_kinematics(arm)
    xyz = np.asarray(xyz, dtype=float)
    seed = np.asarray(seed, dtype=float)
    try:
        direct = np.asarray(
            kinematics.inverse(
                tuple(float(value) for value in xyz),
                seed,
                pitch=float(pitch_rad),
                roll=float(roll_rad),
            ),
            dtype=float,
        )
        if abs(math.degrees(direct[0])) > JOINT1_SAFE_LIMIT_DEG:
            raise ValueError(
                f"joint1 안전 한계 ±{JOINT1_SAFE_LIMIT_DEG:.0f}도 밖"
            )
        return direct
    except ValueError as original_error:
        candidates = []
        limits = getattr(kinematics, "joint_limits", {}) or {}
        joint_names = ("joint1", "joint2", "joint3", "joint4", "joint5")

        for elbow_up in (True, False):
            try:
                raw = np.asarray(
                    kinematics.analytic(
                        xyz,
                        float(pitch_rad),
                        float(roll_rad),
                        elbow_up,
                    ),
                    dtype=float,
                )
            except ValueError:
                continue
            if raw.shape != seed.shape or not np.all(np.isfinite(raw)):
                continue

            candidate = raw.copy()
            candidate[0] = wrap_to_pi(candidate[0])
            if abs(math.degrees(candidate[0])) > JOINT1_SAFE_LIMIT_DEG:
                continue
            bad = [
                name
                for name, value in zip(joint_names, candidate)
                if name in limits
                and not (limits[name][0] <= value <= limits[name][1])
            ]
            if bad:
                continue

            fk_xyz = np.asarray(kinematics.forward(candidate), dtype=float)
            error_mm = float(np.linalg.norm(fk_xyz - xyz) * 1000.0)
            tolerance_mm = max(float(getattr(kinematics, "tol_mm", 1.0)), 1.0)
            if not np.isfinite(error_mm) or error_mm > tolerance_mm:
                continue

            delta = np.arctan2(
                np.sin(candidate - seed), np.cos(candidate - seed)
            )
            candidates.append(
                (float(np.sum(np.abs(delta))), candidate, raw[0], error_mm)
            )

        if not candidates:
            raise original_error

        _score, selected, raw_joint1, error_mm = min(
            candidates, key=lambda item: item[0]
        )
        print(
            "[IK 각도 정규화] joint1 "
            f"{math.degrees(raw_joint1):+.1f}도 -> "
            f"{math.degrees(selected[0]):+.1f}도 / "
            f"FK 오차 {error_mm:.3f} mm"
        )
        return selected


def plan_fixed_pose_stages_from_folded_pose(
    arm, xyz_stages, current_joints, pitch_rad, roll_rad
):
    """Plan a folded joint1 pre-alignment and fixed-pose approach stages."""
    joints_stages = []
    deltas = []
    folded_joints = np.asarray(current_joints, dtype=float)

    first_target = inverse_with_wrapped_joint1(
        arm,
        xyz_stages[0],
        folded_joints,
        pitch_rad,
        roll_rad,
    )
    prealign_joints = folded_joints.copy()
    prealign_joints[0] = first_target[0]
    prealign_delta_deg = abs(
        math.degrees(prealign_joints[0] - folded_joints[0])
    )
    seed = prealign_joints

    for index, xyz in enumerate(xyz_stages):
        target = (
            first_target
            if index == 0
            else inverse_with_wrapped_joint1(
                arm, xyz, seed, pitch_rad, roll_rad
            )
        )
        if target.shape != seed.shape or not np.all(np.isfinite(target)):
            raise ValueError(f"단계 {index + 1} IK 결과가 올바르지 않습니다.")

        delta_deg = np.abs(np.degrees(target - seed))
        max_delta = float(np.max(delta_deg))
        total_delta = float(np.sum(delta_deg))
        if index == 0:
            if max_delta > base.MAX_HIGH_SINGLE_JOINT_CHANGE_DEG:
                raise ValueError(f"80mm 접근 단일 관절 변화 {max_delta:.1f}도")
            if total_delta > base.MAX_HIGH_TOTAL_JOINT_CHANGE_DEG:
                raise ValueError(f"80mm 접근 전체 관절 변화 {total_delta:.1f}도")
        else:
            if max_delta > base.MAX_LOWER_SINGLE_JOINT_CHANGE_DEG:
                raise ValueError(f"하강 단일 관절 변화 {max_delta:.1f}도")
            if total_delta > base.MAX_LOWER_TOTAL_JOINT_CHANGE_DEG:
                raise ValueError(f"하강 전체 관절 변화 {total_delta:.1f}도")

        joints_stages.append(target)
        deltas.append((delta_deg, max_delta, total_delta))
        seed = target
    return prealign_joints, prealign_delta_deg, joints_stages, deltas


def build_rotated_target(
    calibration,
    selected_pixel,
    commanded_offset_deg,
    measured_offset_deg,
    angle_residuals=None,
):
    u, v = selected_pixel
    pixel_inside, pixel_margin = base.inside_hull(
        (u, v), calibration["image_points"]
    )
    if not pixel_inside:
        raise ValueError(
            f"검출 중심이 보정 영상 영역 밖입니다: {pixel_margin:.1f} px"
        )

    raw_reference_xy = base.pixel_to_robot_xy(
        u, v, calibration["homography"]
    )
    central_correction = np.asarray(
        [base.TARGET_X_OFFSET_M, base.TARGET_Y_OFFSET_M], dtype=float
    )
    if angle_residuals is None:
        angle_residuals = load_angle_residuals()
    residual_local = angle_residuals.get(
        int(round(commanded_offset_deg)),
        np.zeros(2, dtype=float),
    )
    corrected_reference_xy = (
        raw_reference_xy + central_correction + residual_local
    )
    reference_inside, reference_margin = base.inside_hull(
        corrected_reference_xy, calibration["robot_points"]
    )
    if not reference_inside:
        raise ValueError(
            "미세보정 후 기준 좌표가 9점 영역 밖입니다: "
            f"{reference_margin * 1000:.1f} mm"
        )

    world_raw_xy = rotate_xy(raw_reference_xy, measured_offset_deg)
    world_central_corrected_xy = rotate_xy(
        raw_reference_xy + central_correction, measured_offset_deg
    )
    world_target_xy = rotate_xy(corrected_reference_xy, measured_offset_deg)
    world_correction = world_target_xy - world_raw_xy
    world_residual = world_target_xy - world_central_corrected_xy

    floor_z = base.floor_z_at(
        float(world_target_xy[0]),
        float(world_target_xy[1]),
        calibration["floor_coefficients"],
    )
    planned_grasp_z = (
        floor_z
        + calibration["grasp_offset_m"]
        + base.VINE_AVOIDANCE_Z_OFFSET_M
    )
    xyz_stages = [
        np.asarray(
            [
                world_target_xy[0],
                world_target_xy[1],
                planned_grasp_z + clearance,
            ],
            dtype=float,
        )
        for clearance in APPROACH_CLEARANCES_M
    ]
    return {
        "pixel": (float(u), float(v)),
        "raw_reference_xy": raw_reference_xy,
        "corrected_reference_xy": corrected_reference_xy,
        "residual_local": residual_local,
        "reference_margin_m": reference_margin,
        "world_raw_xy": world_raw_xy,
        "world_target_xy": world_target_xy,
        "world_correction": world_correction,
        "world_residual": world_residual,
        "floor_z": floor_z,
        "planned_grasp_z": planned_grasp_z,
        "xyz_stages": xyz_stages,
    }


def print_plan(
    target,
    commanded_offset_deg,
    measured_offset_deg,
    calibration,
    current_joints,
    prealign_joints,
    prealign_delta_deg,
    joints_stages,
    deltas,
):
    print("\n========== 다각도 비접촉 접근 계획 ==========")
    print(
        f"촬영각: 명령 {commanded_offset_deg:+.0f}도 / "
        f"실측 {measured_offset_deg:+.2f}도"
    )
    print(f"검출 기준: {base.TARGET_PIXEL_MODE}")
    print(
        f"안정화 픽셀: u={target['pixel'][0]:.1f}, "
        f"v={target['pixel'][1]:.1f}"
    )
    print(
        "중앙 기준 원본 XY [m]: "
        f"x={target['raw_reference_xy'][0]:.4f}, "
        f"y={target['raw_reference_xy'][1]:.4f}"
    )
    print(
        "회전 후 원본 XY [m]: "
        f"x={target['world_raw_xy'][0]:.4f}, "
        f"y={target['world_raw_xy'][1]:.4f}"
    )
    print(
        "각도별 로컬 잔여보정: "
        f"dx={target['residual_local'][0] * 1000:+.1f} mm, "
        f"dy={target['residual_local'][1] * 1000:+.1f} mm"
    )
    print(
        "회전된 잔여보정: "
        f"dx={target['world_residual'][0] * 1000:+.1f} mm, "
        f"dy={target['world_residual'][1] * 1000:+.1f} mm"
    )
    print(
        "회전된 전체 보정: "
        f"dx={target['world_correction'][0] * 1000:+.1f} mm, "
        f"dy={target['world_correction'][1] * 1000:+.1f} mm"
    )
    print(
        "최종 목표 XY [m]: "
        f"x={target['world_target_xy'][0]:.4f}, "
        f"y={target['world_target_xy'][1]:.4f}"
    )
    print(
        f"중앙 기준 보정 영역 경계 여유: "
        f"{target['reference_margin_m'] * 1000:.1f} mm"
    )
    print(f"계산 바닥 z: {target['floor_z']:.4f} m")
    print(f"넝쿨 회피 포함 계획 집기 z: {target['planned_grasp_z']:.4f} m")
    print(f"고정 pitch: {np.degrees(calibration['pitch_rad']):.1f}도")
    print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
    print(
        "수확방향 사전정렬 관절 [deg]: "
        f"{np.round(np.degrees(prealign_joints), 1)}"
    )
    print(f"접힌 자세 joint1 사전정렬 변화: {prealign_delta_deg:.1f}도")

    for index, (clearance, xyz, joints, delta) in enumerate(
        zip(
            APPROACH_CLEARANCES_M,
            target["xyz_stages"],
            joints_stages,
            deltas,
        ),
        start=1,
    ):
        delta_deg, max_delta, _total_delta = delta
        print(
            f"단계 {index}: 계획 집기점보다 {clearance * 1000:.0f}mm 위 / "
            f"XYZ={np.round(xyz, 4)}"
        )
        print(f"  관절 [deg]: {np.round(np.degrees(joints), 1)}")
        print(
            f"  이전 자세 대비 변화 [deg]: {np.round(delta_deg, 1)} "
            f"(최대 {max_delta:.1f}도)"
        )

    print("그리퍼 동작 없음 / 계획 집기점보다 30mm 아래로 내려가지 않음")
    print("============================================")


def return_from_stage_to_central(
    arm, calibration, prealign_joints, joints_stages, current_stage
):
    for index in range(current_stage - 1, -1, -1):
        clearance_mm = APPROACH_CLEARANCES_M[index] * 1000
        print(f"계획 집기점 +{clearance_mm:.0f} mm로 복귀합니다.")
        arm.move_joints(joints_stages[index], duration=LOWER_MOVE_DURATION_SEC)
    print("80mm 상공에서 수확방향 접힘 자세로 복귀합니다.")
    arm.move_joints(prealign_joints, duration=RETURN_DURATION_SEC)
    joint1_delta_deg = math.degrees(
        prealign_joints[0] - calibration["camera_joints"][0]
    )
    print("팔을 접은 상태에서 중앙 안전 자세로 복귀합니다.")
    arm.move_joints(
        calibration["camera_joints"],
        duration=movement_duration(joint1_delta_deg),
    )


def main() -> None:
    arm = None
    cap = None
    calibration = None
    at_central_pose = False

    try:
        calibration = base.load_calibrations()
        angle_residuals = load_angle_residuals()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 프로그램은 선택한 촬영각 하나를 비접촉으로 검증합니다.")
        print("그리퍼는 작동하지 않으며 30mm 상공까지만 접근합니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        print("중앙 보정 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=base.CAMERA_MOVE_DURATION_SEC)
        time.sleep(base.SETTLE_TIME_SEC)
        at_central_pose = True
        print(f"중앙 joint1 절대각도: {base_joint1_deg:.2f}도")

        commanded_offset_deg = ask_offset()
        if commanded_offset_deg is None:
            raise TestCancelled

        target_joint1_deg = base_joint1_deg + commanded_offset_deg
        if abs(target_joint1_deg) > JOINT1_SAFE_LIMIT_DEG:
            raise ValueError(
                f"촬영 joint1={target_joint1_deg:.1f}도가 "
                f"안전 한계 ±{JOINT1_SAFE_LIMIT_DEG:.0f}도를 벗어납니다."
            )

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        duration = movement_duration(commanded_offset_deg)
        print(
            f"촬영 offset={commanded_offset_deg:+.0f}도로 "
            f"{duration:.1f}초 동안 이동합니다."
        )
        at_central_pose = False
        arm.move_joints(view_joints, duration=duration)
        time.sleep(base.SETTLE_TIME_SEC)

        measured_joints = np.asarray(arm.joints(), dtype=float)
        measured_joint1_deg = float(np.degrees(measured_joints[0]))
        measured_offset_deg = measured_joint1_deg - base_joint1_deg
        print(
            f"실측 joint1={measured_joint1_deg:.2f}도 / "
            f"중앙 대비={measured_offset_deg:+.2f}도"
        )

        print("현재 촬영 화면 안의 보정 영역에 호박 하나만 놓으세요.")
        selected = base.choose_pumpkin(model, cap, calibration)
        cap.release()
        cap = None
        cv2.destroyAllWindows()
        if selected is None:
            print("목표 선택을 취소했습니다. 중앙 자세로 돌아갑니다.")
            arm.move_joints(camera_joints, duration=movement_duration(measured_offset_deg))
            at_central_pose = True
            return

        try:
            target = build_rotated_target(
                calibration,
                selected,
                commanded_offset_deg,
                measured_offset_deg,
                angle_residuals,
            )
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 베이스 기준 목표 좌표를 만들지 못했습니다: {error}")
            print("중앙 카메라 자세로 돌아갑니다.")
            arm.move_joints(
                camera_joints,
                duration=movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        print(
            "촬영 자세에서 베이스 기준 목표 XY를 확정했습니다: "
            f"x={target['world_target_xy'][0]:.4f}, "
            f"y={target['world_target_xy'][1]:.4f} m"
        )
        print("현재 촬영 접힘 자세에서 바로 수확 IK를 계산합니다.")
        current_joints = np.asarray(arm.joints(), dtype=float)
        try:
            (
                prealign_joints,
                prealign_delta_deg,
                joints_stages,
                deltas,
            ) = plan_fixed_pose_stages_from_folded_pose(
                arm,
                target["xyz_stages"],
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 안전 IK를 만들지 못했습니다: {error}")
            print("강제 이동하지 않고 중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        print_plan(
            target,
            commanded_offset_deg,
            measured_offset_deg,
            calibration,
            current_joints,
            prealign_joints,
            prealign_delta_deg,
            joints_stages,
            deltas,
        )

        confirmation = input(
            "사람·케이블을 치우고 접힌 채 수확방향으로 돌리려면 PREALIGN 입력: "
        ).strip()
        if confirmation != "PREALIGN":
            print("PREALIGN이 입력되지 않아 이동하지 않습니다.")
            arm.move_joints(
                camera_joints,
                duration=movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        at_central_pose = False
        arm.move_joints(
            prealign_joints,
            duration=movement_duration(prealign_delta_deg),
        )
        print("수확방향 사전정렬 완료. 팔은 접힌 자세입니다.")

        confirmation = input(
            "주변이 안전하면 80mm 상공으로 이동하려면 MOVE_HIGH 입력: "
        ).strip()
        if confirmation != "MOVE_HIGH":
            print("MOVE_HIGH가 입력되지 않아 이동하지 않습니다.")
            arm.move_joints(
                camera_joints,
                duration=movement_duration(
                    math.degrees(prealign_joints[0] - camera_joints[0])
                ),
            )
            at_central_pose = True
            return

        arm.move_joints(joints_stages[0], duration=HIGH_MOVE_DURATION_SEC)
        current_stage = 0
        print("80mm 상공 도착. 중심과 주변 간섭을 확인하세요.")

        confirmation = input(
            "정렬·주변이 안전하면 30mm 상공으로 바로 낮추려면 MOVE_30 입력: "
        ).strip()
        if confirmation != "MOVE_30":
            print("30mm로 내려가지 않고 중앙 자세로 복귀합니다.")
            return_from_stage_to_central(
                arm,
                calibration,
                prealign_joints,
                joints_stages,
                current_stage,
            )
            at_central_pose = True
            return

        arm.move_joints(joints_stages[1], duration=LOWER_MOVE_DURATION_SEC)
        current_stage = 1
        print("30mm 상공 도착. 그리퍼 중심과 호박 중심의 오차를 확인하세요.")
        input("확인이 끝나면 Enter를 눌러 단계적으로 복귀: ")

        return_from_stage_to_central(
            arm,
            calibration,
            prealign_joints,
            joints_stages,
            current_stage,
        )
        at_central_pose = True
        print(
            f"촬영각 {commanded_offset_deg:+.0f}도 비접촉 검증이 끝났습니다."
        )

    except TestCancelled:
        print("검증을 취소했습니다.")
    except KeyboardInterrupt:
        at_central_pose = False
        print("\n사용자가 중단했습니다. 자동 이동을 생략합니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if at_central_pose:
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "자동 정리 자세를 생략합니다. 로봇이 멈췄는지 확인하고 "
                        "필요하면 팔을 받치세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
