#!/usr/bin/env python3
"""Grasp one pumpkin from a calibrated scan angle and lift it 30 mm.

The operator selects one calibrated joint1 scan offset. Detection is performed
in that folded scan pose, the saved per-angle XY residual is applied, and IK is
planned immediately without first returning to the central pose. The arm then
grasps one pumpkin, lifts it only 30 mm, returns it to the same spot, releases
it, and retreats safely. There is no bin transport.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from .. import pumpkin_detected_approach_validation as base
from .. import pumpkin_multiangle_approach_validation as multi


APPROACH_CLEARANCES_M = (0.080, 0.030, 0.010, 0.000)
GRIPPER_OPEN_DURATION_SEC = 3.0
GRIPPER_CLOSE_DURATION_SEC = 4.0
HIGH_MOVE_DURATION_SEC = 12.0
LOWER_MOVE_DURATION_SEC = 8.0
LIFT_STEP_DURATION_SEC = 6.0
RETURN_DURATION_SEC = 12.0


class TestCancelled(Exception):
    """Raised when the operator cancels before target motion."""


def require_command(prompt: str, expected: str) -> None:
    while True:
        value = input(prompt).strip()
        if value == expected:
            return
        print(f"{expected}를 정확히 입력해야 다음 단계로 진행합니다.")


def make_full_grasp_target(target: dict) -> dict:
    grasp_z = float(target["planned_grasp_z"])
    x, y = (float(value) for value in target["world_target_xy"])
    result = dict(target)
    result["xyz_stages"] = [
        np.asarray([x, y, grasp_z + clearance], dtype=float)
        for clearance in APPROACH_CLEARANCES_M
    ]
    return result


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
    print("\n========== 다각도 단일 집기·30mm 상승 계획 ==========")
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
        "각도별 로컬 잔여보정: "
        f"dx={target['residual_local'][0] * 1000:+.1f} mm, "
        f"dy={target['residual_local'][1] * 1000:+.1f} mm"
    )
    print(
        "최종 목표 XY [m]: "
        f"x={target['world_target_xy'][0]:.4f}, "
        f"y={target['world_target_xy'][1]:.4f}"
    )
    print(f"계산 바닥 z: {target['floor_z']:.4f} m")
    print(f"넝쿨 회피 포함 집기 z: {target['planned_grasp_z']:.4f} m")
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
        label = (
            "계획 집기 높이"
            if clearance == 0.0
            else f"집기점 +{clearance * 1000:.0f}mm"
        )
        print(f"단계 {index}: {label} / XYZ={np.round(xyz, 4)}")
        print(f"  관절 [deg]: {np.round(np.degrees(joints), 1)}")
        print(
            f"  이전 자세 대비 변화 [deg]: {np.round(delta_deg, 1)} "
            f"(최대 {max_delta:.1f}도)"
        )

    print("그리퍼: 전류 제한을 사용해 완전히 닫기")
    print("상승: 동일 XY에서 0→10→30mm, 이후 같은 자리에 내려놓기")
    print("수평 이동·적재 없음")
    print("====================================================")


def retreat_to_central(
    arm,
    calibration,
    prealign_joints,
    joints_stages,
    current_stage_index,
):
    """Retreat from the current stage to 80 mm, fold, then return central."""
    for index in range(current_stage_index - 1, -1, -1):
        clearance_mm = APPROACH_CLEARANCES_M[index] * 1000
        print(f"계획 집기점 +{clearance_mm:.0f} mm로 복귀합니다.")
        arm.move_joints(joints_stages[index], duration=LOWER_MOVE_DURATION_SEC)

    print("80mm 상공에서 수확방향 접힘 자세로 복귀합니다.")
    arm.move_joints(prealign_joints, duration=RETURN_DURATION_SEC)
    joint1_delta_deg = np.degrees(
        prealign_joints[0] - calibration["camera_joints"][0]
    )
    print("팔을 접은 상태에서 중앙 안전 자세로 복귀합니다.")
    arm.move_joints(
        calibration["camera_joints"],
        duration=multi.movement_duration(joint1_delta_deg),
    )


def main() -> None:
    arm = None
    cap = None
    calibration = None
    at_central_pose = False
    gripper_released = True

    try:
        calibration = base.load_calibrations()
        angle_residuals = multi.load_angle_residuals()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 프로그램은 선택한 촬영각에서 호박 하나만 실제로 잡습니다.")
        print("30mm만 들었다가 같은 자리에 내려놓으며 적재하지 않습니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        print("중앙 보정 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=base.CAMERA_MOVE_DURATION_SEC)
        time.sleep(base.SETTLE_TIME_SEC)
        at_central_pose = True

        commanded_offset_deg = multi.ask_offset()
        if commanded_offset_deg is None:
            raise TestCancelled
        angle_key = int(round(commanded_offset_deg))
        if angle_key not in angle_residuals:
            raise ValueError(
                f"{angle_key:+d}도 XY 보정값이 없습니다. "
                "먼저 pumpkin_multiangle_xy_micro_adjust.py에서 SAVE하세요."
            )

        target_joint1_deg = base_joint1_deg + commanded_offset_deg
        if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
            raise ValueError(
                f"촬영 joint1={target_joint1_deg:.1f}도가 안전 한계 "
                f"±{multi.JOINT1_SAFE_LIMIT_DEG:.0f}도를 벗어납니다."
            )

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        print(f"촬영 offset={commanded_offset_deg:+.0f}도로 이동합니다.")
        at_central_pose = False
        arm.move_joints(
            view_joints,
            duration=multi.movement_duration(commanded_offset_deg),
        )
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
            raise TestCancelled

        try:
            target = multi.build_rotated_target(
                calibration,
                selected,
                commanded_offset_deg,
                measured_offset_deg,
                angle_residuals,
            )
            target = make_full_grasp_target(target)
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 베이스 기준 목표를 만들지 못했습니다: {error}")
            print("중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        print("현재 촬영 접힘 자세에서 바로 집기 IK를 계산합니다.")
        current_joints = np.asarray(arm.joints(), dtype=float)
        try:
            (
                prealign_joints,
                prealign_delta_deg,
                joints_stages,
                deltas,
            ) = multi.plan_fixed_pose_stages_from_folded_pose(
                arm,
                target["xyz_stages"],
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 안전 IK를 만들지 못했습니다: {error}")
            print("중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(measured_offset_deg),
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

        require_command(
            "사람·케이블을 치우고 접힌 채 수확방향으로 돌리려면 PREALIGN 입력: ",
            "PREALIGN",
        )
        arm.move_joints(
            prealign_joints,
            duration=multi.movement_duration(prealign_delta_deg),
        )
        print("수확방향 사전정렬 완료. 팔은 접힌 자세입니다.")

        require_command(
            "주변이 안전하면 80mm 상공으로 이동하려면 MOVE_HIGH 입력: ",
            "MOVE_HIGH",
        )
        arm.move_joints(joints_stages[0], duration=HIGH_MOVE_DURATION_SEC)
        current_stage = 0
        print("80mm 상공 도착.")

        require_command(
            "그리퍼를 작업 폭으로 열려면 OPEN_GRIPPER 입력: ",
            "OPEN_GRIPPER",
        )
        arm.open_gripper(
            duration=GRIPPER_OPEN_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        print("그리퍼를 작업 폭으로 열었습니다.")

        commands = (
            (1, "MOVE_30", "30mm 상공"),
            (2, "MOVE_10", "10mm 상공"),
            (3, "MOVE_GRASP", "계획 집기 높이"),
        )
        for index, command, label in commands:
            require_command(
                f"정렬·간섭이 안전하면 {label}로 이동하려면 {command} 입력: ",
                command,
            )
            arm.move_joints(
                joints_stages[index], duration=LOWER_MOVE_DURATION_SEC
            )
            current_stage = index
            print(f"{label} 도착. 아직 그리퍼는 열려 있습니다.")

        require_command(
            "전류 제한으로 호박을 실제로 잡으려면 FULL_CLOSE 입력: ",
            "FULL_CLOSE",
        )
        gripper_released = False
        arm.close_gripper(
            duration=GRIPPER_CLOSE_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        print("그리퍼 닫기 완료. 호박 몸통과 넝쿨 상태를 확인하세요.")

        while True:
            confirmation = input(
                "30mm 상승은 LIFT_30 / 상승 없이 열기는 OPEN_NO_LIFT: "
            ).strip()
            if confirmation in {"LIFT_30", "OPEN_NO_LIFT"}:
                break
            print("LIFT_30 또는 OPEN_NO_LIFT를 정확히 입력하세요.")

        if confirmation == "OPEN_NO_LIFT":
            arm.open_gripper(
                duration=GRIPPER_OPEN_DURATION_SEC,
                stall_guard=True,
                wait=True,
            )
            gripper_released = True
            print("상승하지 않고 그리퍼를 열었습니다.")
            retreat_to_central(
                arm,
                calibration,
                prealign_joints,
                joints_stages,
                current_stage,
            )
            at_central_pose = True
            return

        print("동일 XY에서 10mm 상승합니다.")
        arm.move_joints(joints_stages[2], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 2
        print("동일 XY에서 30mm 상승합니다.")
        arm.move_joints(joints_stages[1], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 1
        print("30mm 상승 완료. 수평 이동은 하지 않습니다.")

        require_command(
            "같은 자리에 다시 내려놓으려면 LOWER_BACK 입력: ",
            "LOWER_BACK",
        )
        print("집기점보다 10mm 위로 하강합니다.")
        arm.move_joints(joints_stages[2], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 2
        print("원래 집기 높이까지 하강합니다.")
        arm.move_joints(joints_stages[3], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 3

        require_command(
            "호박을 놓고 그리퍼를 열려면 OPEN_TO_RELEASE 입력: ",
            "OPEN_TO_RELEASE",
        )
        arm.open_gripper(
            duration=GRIPPER_OPEN_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        gripper_released = True
        print("그리퍼를 열었습니다. 호박은 원래 위치에 있습니다.")

        retreat_to_central(
            arm,
            calibration,
            prealign_joints,
            joints_stages,
            current_stage,
        )
        at_central_pose = True
        print("다각도 단일 집기·30mm 상승·원위치 복귀 검증이 끝났습니다.")

    except TestCancelled:
        print("목표 선택을 취소했습니다.")
        if arm is not None and calibration is not None and not at_central_pose:
            measured = np.asarray(arm.joints(), dtype=float)
            delta_deg = np.degrees(
                measured[0] - calibration["camera_joints"][0]
            )
            arm.move_joints(
                calibration["camera_joints"],
                duration=multi.movement_duration(delta_deg),
            )
            at_central_pose = True
    except KeyboardInterrupt:
        at_central_pose = False
        print("\n사용자가 중단했습니다. 자동 이동과 그리퍼 동작을 생략합니다.")
        print("호박을 들고 있다면 팔과 호박을 받쳐 직접 상태를 확인하세요.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if at_central_pose and gripper_released:
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "자동 정리 자세를 생략합니다. 로봇이 멈췄는지 확인하고 "
                        "그리퍼·호박 상태를 직접 확인하세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
