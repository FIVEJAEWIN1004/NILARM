"""Measure the final XY offset at the real fixed-pitch grasp posture.

Run this only after pumpkin_corrected_single_grasp_test.py has produced a
stable affine-corrected target.  The gripper never closes.  The operator moves
the open gripper in small XY increments and saves the offset that visually
aligns the gripper center with the pumpkin center.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from pumpkin_scan_count import (
    JOINT1_SAFE_LIMIT_DEG,
    MODEL_PATH,
    MOVE_DURATION_SEC,
    SETTLE_TIME_SEC,
    load_calibration,
    open_camera,
    validate_model,
)
from pumpkin_corrected_single_grasp_test import (
    APPROACH_DURATION_SEC,
    APPROACH_Z_M,
    GRIPPER_DURATION_SEC,
    LIFT_Z_M,
    RETURN_DURATION_SEC,
    apply_affine,
    ask_offset,
    detect_exactly_one,
    find_complete_plan,
    inside_calibrated_region,
    inverse_at,
    joint_delta,
    load_calibration_points,
    require_exact,
)


FINAL_OFFSET_PATH = Path(__file__).with_name("pumpkin_grasp_final_offset.json")

# LIFT_Z_M is 3 cm above the tested grasp height.  It is close enough to align
# visually but does not command the gripper to touch or close on the pumpkin.
ALIGN_Z_M = LIFT_Z_M
DEFAULT_STEP_M = 0.002
MAX_ABS_OFFSET_M = 0.020
JOG_DURATION_SEC = 2.0
ALIGN_DESCEND_DURATION_SEC = 6.0
MAX_JOG_SINGLE_JOINT_DEG = 12.0
MAX_JOG_TOTAL_DEG = 30.0


def load_existing_result():
    if not FINAL_OFFSET_PATH.is_file():
        return {"samples": []}
    data = json.loads(FINAL_OFFSET_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("samples"), list):
        raise ValueError(f"기존 최종 오프셋 파일 형식이 잘못되었습니다: {FINAL_OFFSET_PATH}")
    return data


def save_offset(raw_xy, affine_xy, final_xy, pitch_deg, offset_deg):
    data = load_existing_result()
    sample_offset = np.asarray(final_xy, dtype=float) - np.asarray(affine_xy, dtype=float)
    sample = {
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "camera_offset_deg": float(offset_deg),
        "pitch_deg": float(pitch_deg),
        "align_z_m": float(ALIGN_Z_M),
        "raw_xy_m": [float(raw_xy[0]), float(raw_xy[1])],
        "affine_xy_m": [float(affine_xy[0]), float(affine_xy[1])],
        "aligned_xy_m": [float(final_xy[0]), float(final_xy[1])],
        "final_offset_m": [float(sample_offset[0]), float(sample_offset[1])],
        "final_offset_mm": [float(sample_offset[0] * 1000), float(sample_offset[1] * 1000)],
    }
    data["samples"].append(sample)

    offsets = np.asarray(
        [item["final_offset_m"] for item in data["samples"]],
        dtype=float,
    )
    median_offset = np.median(offsets, axis=0)
    data["result"] = {
        "method": "componentwise_median",
        "sample_count": int(len(offsets)),
        "offset_m": [float(median_offset[0]), float(median_offset[1])],
        "offset_mm": [float(median_offset[0] * 1000), float(median_offset[1] * 1000)],
    }
    FINAL_OFFSET_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sample, data["result"]


def print_controls(step_m):
    print("\n========== 미세조정 명령 ==========")
    print(f"XP : X +{step_m * 1000:.0f} mm")
    print(f"XM : X -{step_m * 1000:.0f} mm")
    print(f"YP : Y +{step_m * 1000:.0f} mm")
    print(f"YM : Y -{step_m * 1000:.0f} mm")
    print("S1 / S2 / S5 : 이동 간격을 1/2/5 mm로 변경")
    print("ZERO : 이번 실행의 affine 좌표로 되돌아가기")
    print("SAVE : 현재 XY 오프셋 저장 후 종료")
    print("Q : 저장하지 않고 종료")
    print("===================================")


def command_delta(command, step_m):
    mapping = {
        "XP": np.asarray([step_m, 0.0]),
        "XM": np.asarray([-step_m, 0.0]),
        "YP": np.asarray([0.0, step_m]),
        "YM": np.asarray([0.0, -step_m]),
    }
    return mapping.get(command)


def main():
    arm = None
    cap = None
    calibration = None
    camera_joints = None
    safe_motion = False
    at_alignment_height = False
    current_xy = None
    pitch_deg = None

    try:
        calibration_points = load_calibration_points()
        calibration = load_calibration()
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        cap = open_camera(calibration)

        print("이 프로그램은 그리퍼를 닫거나 호박을 들어 올리지 않습니다.")
        print(f"정렬 높이 z={ALIGN_Z_M:.4f} m에서 XY만 미세조정합니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = np.asarray(calibration["camera_joints"], dtype=float)
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)
        safe_motion = True

        offset_deg = ask_offset()
        if offset_deg is None:
            return

        view_joint1_deg = base_joint1_deg + offset_deg
        if abs(view_joint1_deg) > JOINT1_SAFE_LIMIT_DEG:
            raise ValueError(
                f"촬영 joint1={view_joint1_deg:.1f}도가 안전 범위를 벗어납니다."
            )

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(view_joint1_deg)
        print(f"촬영 자세 offset={offset_deg:+.0f}도로 이동합니다.")
        safe_motion = False
        arm.move_joints(view_joints, duration=MOVE_DURATION_SEC)
        safe_motion = True
        time.sleep(SETTLE_TIME_SEC)

        target = detect_exactly_one(model, cap, calibration, offset_deg)
        if target is None:
            return

        raw_xy = np.asarray([target.x, target.y], dtype=float)
        inside, hull_distance = inside_calibrated_region(raw_xy, calibration_points)
        affine_xy = apply_affine(raw_xy)
        current_xy = affine_xy.copy()

        print("\n========== 좌표 확인 ==========")
        print(f"YOLO 원본: x={raw_xy[0]:.4f}, y={raw_xy[1]:.4f} m")
        print(f"affine 보정: x={affine_xy[0]:.4f}, y={affine_xy[1]:.4f} m")
        print(f"표본 영역 경계 거리: {hull_distance * 1000:+.1f} mm")
        print("===============================")
        if not inside:
            print("[이동 금지] 검출 좌표가 보정 표본 영역 밖에 있습니다.")
            return

        cap.release()
        cap = None
        cv2.destroyAllWindows()

        print("IK 계산 전에 중앙 카메라 자세로 돌아갑니다.")
        safe_motion = False
        arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
        safe_motion = True
        time.sleep(SETTLE_TIME_SEC)

        current_joints = np.asarray(arm.joints(), dtype=float)
        plan = find_complete_plan(
            arm,
            float(affine_xy[0]),
            float(affine_xy[1]),
            current_joints,
        )
        if plan is None:
            print("[이동 금지] 동일 pitch의 안전한 IK 계획이 없습니다.")
            return

        pitch_deg = float(plan["pitch_deg"])
        align_joints = inverse_at(
            arm,
            [affine_xy[0], affine_xy[1], ALIGN_Z_M],
            plan["approach"],
            pitch_deg,
        )
        align_delta, align_max, align_total = joint_delta(align_joints, plan["approach"])
        if align_max > 35.0 or align_total > 90.0:
            print(
                "[이동 금지] 정렬 높이 하강 변화량이 큽니다: "
                f"max={align_max:.1f}, total={align_total:.1f}도"
            )
            return

        print("\n========== 정렬 이동 계획 ==========")
        print(f"기준 XY [m]: {np.round(affine_xy, 4)}")
        print(f"고정 pitch: {pitch_deg:.1f}도")
        print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
        print(f"상공 관절 [deg]: {np.round(np.degrees(plan['approach']), 1)}")
        print(f"정렬 관절 [deg]: {np.round(np.degrees(align_joints), 1)}")
        print(f"정렬 하강 변화 [deg]: {np.round(align_delta, 1)}")
        print("그리퍼 닫힘 없음 / 자동 집기 없음")
        print("=====================================")

        if not require_exact(
            "상공으로 이동하려면 MOVE 입력: ",
            "MOVE",
        ):
            return

        arm.open_gripper(duration=GRIPPER_DURATION_SEC, stall_guard=True)
        safe_motion = False
        arm.move_joints(plan["approach"], duration=APPROACH_DURATION_SEC)
        safe_motion = True

        if not require_exact(
            "호박 중심과 안전거리를 확인하고 정렬 높이로 내려가려면 ALIGN 입력: ",
            "ALIGN",
        ):
            return

        safe_motion = False
        arm.move_joints(align_joints, duration=ALIGN_DESCEND_DURATION_SEC)
        safe_motion = True
        at_alignment_height = True
        current_joints = align_joints

        step_m = DEFAULT_STEP_M
        print_controls(step_m)
        while True:
            offset_now = current_xy - affine_xy
            print(
                f"현재 추가 오프셋: dx={offset_now[0] * 1000:+.1f}, "
                f"dy={offset_now[1] * 1000:+.1f} mm | step={step_m * 1000:.0f} mm"
            )
            command = input("명령: ").strip().upper()

            if command in {"S1", "S2", "S5"}:
                step_m = int(command[1:]) / 1000.0
                print_controls(step_m)
                continue

            if command == "SAVE":
                sample, result = save_offset(
                    raw_xy,
                    affine_xy,
                    current_xy,
                    pitch_deg,
                    offset_deg,
                )
                print(
                    "이번 오프셋 저장: "
                    f"dx={sample['final_offset_mm'][0]:+.1f}, "
                    f"dy={sample['final_offset_mm'][1]:+.1f} mm"
                )
                print(
                    f"누적 {result['sample_count']}회 중앙값: "
                    f"dx={result['offset_mm'][0]:+.1f}, "
                    f"dy={result['offset_mm'][1]:+.1f} mm"
                )
                break

            if command == "Q":
                print("저장하지 않고 종료합니다.")
                break

            if command == "ZERO":
                candidate_xy = affine_xy.copy()
            else:
                delta_xy = command_delta(command, step_m)
                if delta_xy is None:
                    print("명령을 다시 입력하세요.")
                    continue
                candidate_xy = current_xy + delta_xy

            total_offset = candidate_xy - affine_xy
            if np.any(np.abs(total_offset) > MAX_ABS_OFFSET_M):
                print("[이동 금지] 추가 오프셋은 각 축 ±20 mm까지만 허용합니다.")
                continue

            try:
                candidate_joints = inverse_at(
                    arm,
                    [candidate_xy[0], candidate_xy[1], ALIGN_Z_M],
                    current_joints,
                    pitch_deg,
                )
            except (ValueError, RuntimeError) as error:
                print(f"[이동 금지] IK 실패: {error}")
                continue

            delta_joints, max_delta, total_delta = joint_delta(
                candidate_joints,
                current_joints,
            )
            if (
                max_delta > MAX_JOG_SINGLE_JOINT_DEG
                or total_delta > MAX_JOG_TOTAL_DEG
            ):
                print(
                    "[이동 금지] 미세이동 관절 변화량이 큽니다: "
                    f"max={max_delta:.1f}, total={total_delta:.1f}도"
                )
                continue

            print(
                f"이동: x={candidate_xy[0]:.4f}, y={candidate_xy[1]:.4f} m, "
                f"관절 최대 변화={max_delta:.1f}도"
            )
            safe_motion = False
            arm.move_joints(candidate_joints, duration=JOG_DURATION_SEC)
            safe_motion = True
            current_xy = candidate_xy
            current_joints = candidate_joints

        # Always retreat vertically at the final adjusted XY before returning.
        retreat_joints = inverse_at(
            arm,
            [current_xy[0], current_xy[1], APPROACH_Z_M],
            current_joints,
            pitch_deg,
        )
        print("현재 XY에서 상공으로 빠져나옵니다.")
        safe_motion = False
        arm.move_joints(retreat_joints, duration=ALIGN_DESCEND_DURATION_SEC)
        at_alignment_height = False
        safe_motion = True

        print("중앙 카메라 자세로 복귀합니다.")
        safe_motion = False
        arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
        safe_motion = True
        print(f"결과 파일: {FINAL_OFFSET_PATH}")

    except KeyboardInterrupt:
        safe_motion = False
        print("\n사용자가 미세조정을 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if safe_motion and at_alignment_height and current_xy is not None:
                    try:
                        retreat_joints = inverse_at(
                            arm,
                            [current_xy[0], current_xy[1], APPROACH_Z_M],
                            np.asarray(arm.joints(), dtype=float),
                            pitch_deg,
                        )
                        print("정렬 높이에서 상공으로 먼저 빠져나옵니다.")
                        arm.move_joints(
                            retreat_joints,
                            duration=ALIGN_DESCEND_DURATION_SEC,
                        )
                        at_alignment_height = False
                    except (ValueError, RuntimeError) as error:
                        safe_motion = False
                        print(f"안전 상공 복귀 계산 실패: {error}")

                if safe_motion and not at_alignment_height and camera_joints is not None:
                    print("중앙 카메라 자세로 돌아갑니다.")
                    arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "자동 복귀를 생략합니다. 로봇이 정지했는지 확인하고 "
                        "팔을 받치세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")


if __name__ == "__main__":
    main()
