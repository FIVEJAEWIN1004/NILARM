#!/usr/bin/env python3
"""Partially close around one detected pumpkin without lifting it.

This script depends on pumpkin_detected_approach_validation.py and reuses its
verified camera, YOLO, 9-point plane, +10 mm robot-forward XY correction,
taught grasp pose, and +10 mm vine-avoidance height.  Motion is staged and
every lower step requires an exact confirmation word.

The gripper is opened at the 80 mm approach pose, descends to the planned
grasp pose, closes only to 45% open, then must be reopened before retreat.
It never lifts the pumpkin and never calls close_gripper().
"""

from __future__ import annotations

import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
import pumpkin_detected_approach_validation as base


# Clearances above the planned grasp pose.  Zero is the final no-lift pose.
APPROACH_CLEARANCES_M = (0.080, 0.050, 0.030, 0.010, 0.000)
STAGE_COMMANDS = ("MOVE_HIGH", "MOVE_50", "MOVE_30", "MOVE_10", "MOVE_GRASP")

# OmxFollower.gripper(): 0.0=closed, 1.0=open.
# Stop at 0.45 for this first contact test; do not fully close.
PARTIAL_CLOSE_VALUE = 0.45
GRIPPER_OPEN_DURATION_SEC = 3.0
PARTIAL_CLOSE_DURATION_SEC = 4.0

HIGH_MOVE_DURATION_SEC = 12.0
LOWER_MOVE_DURATION_SEC = 8.0
RETURN_DURATION_SEC = 12.0


class TestCancelled(Exception):
    """Raised when the operator cancels before target motion."""


def build_target(calibration, selected_pixel):
    u, v = selected_pixel
    raw_xy = base.pixel_to_robot_xy(u, v, calibration["homography"])
    target_xy = raw_xy + np.asarray(
        [base.TARGET_X_OFFSET_M, base.TARGET_Y_OFFSET_M], dtype=float
    )

    pixel_inside, pixel_margin = base.inside_hull(
        (u, v), calibration["image_points"]
    )
    if not pixel_inside:
        raise ValueError(
            f"검출 중심이 보정 영상 영역 밖입니다: {pixel_margin:.1f} px"
        )

    xy_inside, xy_margin = base.inside_hull(
        target_xy, calibration["robot_points"]
    )
    if not xy_inside:
        raise ValueError(
            f"미세보정 후 XY가 보정 영역 밖입니다: {xy_margin * 1000:.1f} mm"
        )

    floor_z = base.floor_z_at(
        float(target_xy[0]),
        float(target_xy[1]),
        calibration["floor_coefficients"],
    )
    grasp_z = (
        floor_z
        + calibration["grasp_offset_m"]
        + base.VINE_AVOIDANCE_Z_OFFSET_M
    )
    xyz_stages = [
        np.asarray(
            [target_xy[0], target_xy[1], grasp_z + clearance], dtype=float
        )
        for clearance in APPROACH_CLEARANCES_M
    ]
    return {
        "pixel": (float(u), float(v)),
        "raw_xy": raw_xy,
        "target_xy": target_xy,
        "xy_margin_m": xy_margin,
        "floor_z": floor_z,
        "grasp_z": grasp_z,
        "xyz_stages": xyz_stages,
    }


def print_plan(target, calibration, current_joints, joints_stages, deltas):
    print("\n========== 부분 닫기 시험 계획 ==========")
    print(f"검출 기준: {base.TARGET_PIXEL_MODE}")
    print(
        f"안정화 픽셀: u={target['pixel'][0]:.1f}, "
        f"v={target['pixel'][1]:.1f}"
    )
    print(
        f"원본 변환 XY [m]: x={target['raw_xy'][0]:.4f}, "
        f"y={target['raw_xy'][1]:.4f}"
    )
    print(
        "실측 미세보정: "
        f"dx={base.TARGET_X_OFFSET_M * 1000:+.1f} mm, "
        f"dy={base.TARGET_Y_OFFSET_M * 1000:+.1f} mm"
    )
    print(
        f"최종 목표 XY [m]: x={target['target_xy'][0]:.4f}, "
        f"y={target['target_xy'][1]:.4f}"
    )
    print(f"보정 영역 경계 여유: {target['xy_margin_m'] * 1000:.1f} mm")
    print(f"계산 바닥 z: {target['floor_z']:.4f} m")
    print(f"넝쿨 회피 포함 계획 집기 z: {target['grasp_z']:.4f} m")
    print(f"고정 pitch: {np.degrees(calibration['pitch_rad']):.1f}도")
    print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")

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
        label = "계획 집기 높이" if clearance == 0.0 else f"집기점 +{clearance * 1000:.0f}mm"
        print(f"단계 {index}: {label} / XYZ={np.round(xyz, 4)}")
        print(f"  관절 [deg]: {np.round(np.degrees(joints), 1)}")
        print(
            f"  이전 자세 대비 변화 [deg]: {np.round(delta_deg, 1)} "
            f"(최대 {max_delta:.1f}도)"
        )

    print(
        f"그리퍼: 완전 닫힘 0.0이 아닌 {PARTIAL_CLOSE_VALUE:.2f}까지만 닫기"
    )
    print("상승 동작 없음 / 부분 닫기 후 다시 열어야만 복귀")
    print("========================================")


def retreat_to_camera(arm, calibration, joints_stages, current_stage_index):
    """Retreat through every already-validated higher pose."""
    for index in range(current_stage_index - 1, -1, -1):
        clearance_mm = APPROACH_CLEARANCES_M[index] * 1000
        print(f"계획 집기점 +{clearance_mm:.0f} mm로 복귀합니다.")
        arm.move_joints(joints_stages[index], duration=LOWER_MOVE_DURATION_SEC)

    print("중앙 카메라 자세로 복귀합니다.")
    arm.move_joints(
        calibration["camera_joints"], duration=RETURN_DURATION_SEC
    )


def main() -> None:
    arm = None
    cap = None
    calibration = None
    at_camera_pose = False
    gripper_released = True

    try:
        calibration = base.load_calibrations()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 시험은 호박을 들어 올리지 않습니다.")
        print(
            f"그리퍼는 {PARTIAL_CLOSE_VALUE:.2f}까지만 닫고 전류 제한을 사용합니다."
        )
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("중앙 보정 카메라 자세로 이동합니다.")
        arm.move_joints(
            calibration["camera_joints"], duration=base.CAMERA_MOVE_DURATION_SEC
        )
        time.sleep(base.SETTLE_TIME_SEC)
        at_camera_pose = True

        selected = base.choose_pumpkin(model, cap, calibration)
        cap.release()
        cap = None
        cv2.destroyAllWindows()
        if selected is None:
            raise TestCancelled

        target = build_target(calibration, selected)
        current_joints = np.asarray(arm.joints(), dtype=float)
        try:
            joints_stages, deltas = base.plan_fixed_pose_stages(
                arm,
                target["xyz_stages"],
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 안전 IK를 만들지 못했습니다: {error}")
            return

        print_plan(target, calibration, current_joints, joints_stages, deltas)

        confirmation = input(
            "사람·케이블을 치우고 80mm 상공으로 이동하려면 MOVE_HIGH 입력: "
        ).strip()
        if confirmation != STAGE_COMMANDS[0]:
            print("MOVE_HIGH가 입력되지 않아 이동하지 않습니다.")
            return

        at_camera_pose = False
        arm.move_joints(joints_stages[0], duration=HIGH_MOVE_DURATION_SEC)
        current_stage = 0
        print("80mm 상공 도착. 중심과 주변 간섭을 확인하세요.")

        confirmation = input(
            "주변이 비어 있고 그리퍼를 작업 폭으로 열려면 OPEN_GRIPPER 입력: "
        ).strip()
        if confirmation != "OPEN_GRIPPER":
            print("그리퍼를 열지 않고 복귀합니다.")
            retreat_to_camera(arm, calibration, joints_stages, current_stage)
            at_camera_pose = True
            return

        arm.open_gripper(
            duration=GRIPPER_OPEN_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        gripper_released = True
        print("그리퍼를 작업 폭으로 열었습니다.")

        prompts = (
            "정렬이 맞고 50mm 상공으로 낮추려면 MOVE_50 입력: ",
            "정렬·높이가 안전하고 30mm 상공으로 낮추려면 MOVE_30 입력: ",
            "간섭이 없고 10mm 상공으로 낮추려면 MOVE_10 입력: ",
            "호박·넝쿨 위치가 안전하고 집기 높이로 낮추려면 MOVE_GRASP 입력: ",
        )

        for index, prompt in enumerate(prompts, start=1):
            confirmation = input(prompt).strip()
            if confirmation != STAGE_COMMANDS[index]:
                print(
                    f"{STAGE_COMMANDS[index]}가 입력되지 않아 더 내려가지 않고 복귀합니다."
                )
                retreat_to_camera(arm, calibration, joints_stages, current_stage)
                at_camera_pose = True
                return
            arm.move_joints(joints_stages[index], duration=LOWER_MOVE_DURATION_SEC)
            current_stage = index
            if APPROACH_CLEARANCES_M[index] > 0.0:
                print(
                    f"계획 집기점보다 {APPROACH_CLEARANCES_M[index] * 1000:.0f}mm "
                    "위에 도착했습니다."
                )
            else:
                print("계획 집기 높이에 도착했습니다. 아직 그리퍼는 열려 있습니다.")

        confirmation = input(
            f"상승 없이 그리퍼를 {PARTIAL_CLOSE_VALUE:.2f}까지만 닫으려면 "
            "PARTIAL_CLOSE 입력: "
        ).strip()
        if confirmation != "PARTIAL_CLOSE":
            print("그리퍼를 닫지 않고 복귀합니다.")
            retreat_to_camera(arm, calibration, joints_stages, current_stage)
            at_camera_pose = True
            return

        gripper_released = False
        arm.gripper(
            PARTIAL_CLOSE_VALUE,
            duration=PARTIAL_CLOSE_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        print("부분 닫기 완료. 로봇팔은 상승하지 않습니다.")
        print("호박 몸통 접촉 여부와 넝쿨이 끼지 않았는지 확인하세요.")

        while True:
            confirmation = input(
                "시험을 끝내고 그리퍼를 다시 열려면 OPEN_TO_RELEASE 입력: "
            ).strip()
            if confirmation == "OPEN_TO_RELEASE":
                break
            print("그리퍼를 연 뒤에만 자동 복귀할 수 있습니다.")

        arm.open_gripper(
            duration=GRIPPER_OPEN_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        gripper_released = True
        print("그리퍼를 다시 열었습니다. 호박은 들어 올리지 않았습니다.")

        retreat_to_camera(arm, calibration, joints_stages, current_stage)
        at_camera_pose = True
        print("부분 닫기 검증이 끝났습니다.")

    except TestCancelled:
        print("목표 선택을 취소했습니다.")
    except KeyboardInterrupt:
        at_camera_pose = False
        print("\n사용자가 중단했습니다. 자동 이동과 그리퍼 동작을 생략합니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if at_camera_pose and gripper_released:
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "자동 정리 자세를 생략합니다. 로봇이 멈췄는지 확인하고 "
                        "그리퍼와 호박 상태를 직접 확인하세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
