"""Affine-corrected, one-pumpkin grasp test for OMX.

This is deliberately a single-target test, not an automatic harvest program.
It detects exactly one pumpkin, applies the measured affine XY correction,
pre-computes approach/grasp/lift IK with one fixed pitch, and requires a
separate typed confirmation before every hazardous motion.
"""

import json
import math
import time
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
    observe_view,
    open_camera,
    valid_clusters,
    validate_model,
)


CORRECTION_PATH = Path(__file__).with_name("pumpkin_grasp_xy_correction.json")

# Measured from the 12 teach samples (RMS 5.26 mm, max 10.56 mm).
AFFINE_MATRIX = np.asarray(
    [
        [1.1051267244661236, -0.0025138941678093368],
        [0.007918657993872409, 1.103073937735045],
    ],
    dtype=float,
)
AFFINE_BIAS_M = np.asarray(
    [-0.010997945904720295, -0.000782674047971112],
    dtype=float,
)

ALLOWED_OFFSETS_DEG = (-140, -110, -80, -50, -20, 0, 10, 40, 70, 100, 130, 140)
PITCH_CANDIDATES_DEG = (85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35)

# Raised from the old floor-level grasp (-0.0062 m) to avoid the vines.
GRASP_Z_M = 0.0063
APPROACH_Z_M = GRASP_Z_M + 0.080
LIFT_Z_M = GRASP_Z_M + 0.030

APPROACH_DURATION_SEC = 12.0
DESCEND_DURATION_SEC = 8.0
LIFT_DURATION_SEC = 6.0
LOWER_DURATION_SEC = 6.0
RETURN_DURATION_SEC = 12.0
GRIPPER_DURATION_SEC = 3.0

MAX_SINGLE_JOINT_CHANGE_DEG = 65.0
MAX_TOTAL_JOINT_CHANGE_DEG = 170.0
MAX_DESCENT_JOINT_CHANGE_DEG = 35.0
MAX_DESCENT_TOTAL_CHANGE_DEG = 90.0
CALIBRATION_HULL_MARGIN_M = 0.005


def load_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"필요한 파일이 없습니다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_calibration_points():
    data = load_json(CORRECTION_PATH)
    samples = data.get("samples", [])
    if len(samples) < 3:
        raise ValueError("XY 보정 표본이 3개보다 적습니다.")
    points = np.asarray(
        [sample["predicted_xy_m"] for sample in samples],
        dtype=np.float32,
    )
    if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
        raise ValueError("XY 보정 표본 좌표가 올바르지 않습니다.")
    return points


def inside_calibrated_region(point_xy, calibration_points):
    hull = cv2.convexHull(calibration_points.reshape(-1, 1, 2))
    distance = cv2.pointPolygonTest(
        hull,
        (float(point_xy[0]), float(point_xy[1])),
        True,
    )
    return distance >= -CALIBRATION_HULL_MARGIN_M, float(distance)


def apply_affine(point_xy):
    return AFFINE_MATRIX @ np.asarray(point_xy, dtype=float) + AFFINE_BIAS_M


def ask_offset():
    allowed = ", ".join(f"{value:+d}" for value in ALLOWED_OFFSETS_DEG)
    while True:
        text = input(
            "\n호박이 보이는 촬영 offset을 입력하세요\n"
            f"사용 가능: {allowed}\n"
            "offset [deg] (종료 Q): "
        ).strip()
        if text.upper() == "Q":
            return None
        try:
            value = int(text)
        except ValueError:
            print("정수 각도를 입력하세요.")
            continue
        if value not in ALLOWED_OFFSETS_DEG:
            print("목록에 있는 각도를 입력하세요.")
            continue
        return float(value)


def detect_exactly_one(model, cap, calibration, offset_deg):
    clusters = []
    count, stop_requested = observe_view(
        model,
        cap,
        calibration,
        offset_deg,
        0,
        clusters,
        {"show_total": True},
    )
    cv2.destroyAllWindows()
    if stop_requested:
        return None

    targets = list(valid_clusters(clusters))
    if count != 1 or len(targets) != 1:
        print(
            f"[중단] 화면 검출={count}개, 유효 좌표={len(targets)}개입니다. "
            "호박 하나만 보이게 하고 다시 실행하세요."
        )
        return None
    return targets[0]


def get_kinematics(arm):
    kinematics = getattr(arm, "kin", None)
    if kinematics is None:
        kinematics = getattr(arm, "_kin", None)
    if kinematics is None or not hasattr(kinematics, "inverse"):
        raise RuntimeError("OmxFollower에서 inverse kinematics를 찾지 못했습니다.")
    return kinematics


def inverse_at(arm, xyz, seed_joints, pitch_deg):
    joints = np.asarray(
        get_kinematics(arm).inverse(
            tuple(float(value) for value in xyz),
            np.asarray(seed_joints, dtype=float),
            pitch=np.radians(float(pitch_deg)),
            roll=0.0,
        ),
        dtype=float,
    )
    if joints.shape != np.asarray(seed_joints).shape or not np.all(np.isfinite(joints)):
        raise ValueError("IK가 유효한 관절 배열을 반환하지 않았습니다.")
    return joints


def joint_delta(target, start):
    delta = np.abs(np.degrees(np.asarray(target) - np.asarray(start)))
    return delta, float(np.max(delta)), float(np.sum(delta))


def find_complete_plan(arm, x, y, current_joints):
    """Choose one pitch that safely reaches approach, grasp, and lift."""
    candidates = []
    failures = []

    approach_xyz = np.asarray([x, y, APPROACH_Z_M], dtype=float)
    grasp_xyz = np.asarray([x, y, GRASP_Z_M], dtype=float)
    lift_xyz = np.asarray([x, y, LIFT_Z_M], dtype=float)

    for pitch_deg in PITCH_CANDIDATES_DEG:
        try:
            approach = inverse_at(arm, approach_xyz, current_joints, pitch_deg)
            d0, max0, total0 = joint_delta(approach, current_joints)
            if max0 > MAX_SINGLE_JOINT_CHANGE_DEG or total0 > MAX_TOTAL_JOINT_CHANGE_DEG:
                raise ValueError(
                    f"상공 변화량 초과(max={max0:.1f}, total={total0:.1f}도)"
                )

            grasp = inverse_at(arm, grasp_xyz, approach, pitch_deg)
            d1, max1, total1 = joint_delta(grasp, approach)
            if max1 > MAX_DESCENT_JOINT_CHANGE_DEG or total1 > MAX_DESCENT_TOTAL_CHANGE_DEG:
                raise ValueError(
                    f"하강 변화량 초과(max={max1:.1f}, total={total1:.1f}도)"
                )

            lift = inverse_at(arm, lift_xyz, grasp, pitch_deg)
            d2, max2, total2 = joint_delta(lift, grasp)
            if max2 > MAX_DESCENT_JOINT_CHANGE_DEG or total2 > MAX_DESCENT_TOTAL_CHANGE_DEG:
                raise ValueError(
                    f"상승 변화량 초과(max={max2:.1f}, total={total2:.1f}도)"
                )

            score = max0 + 0.15 * total0 + 0.25 * max1 + 0.25 * max2
            candidates.append(
                {
                    "pitch_deg": float(pitch_deg),
                    "approach": approach,
                    "grasp": grasp,
                    "lift": lift,
                    "approach_delta": d0,
                    "descent_delta": d1,
                    "lift_delta": d2,
                    "score": score,
                }
            )
        except (ValueError, RuntimeError) as error:
            failures.append((pitch_deg, str(error)))

    if not candidates:
        print("\n[IK 실패 내역]")
        for pitch_deg, reason in failures:
            print(f"  pitch={pitch_deg:>2}도: {reason}")
        return None
    return min(candidates, key=lambda item: item["score"])


def require_exact(prompt, expected):
    value = input(prompt).strip()
    if value != expected:
        print(f"'{expected}'가 입력되지 않아 동작을 취소합니다.")
        return False
    return True


def main():
    arm = None
    cap = None
    calibration = None
    safe_return_allowed = False
    holding = False
    retreat_joints = None
    retreat_needed = False

    try:
        calibration_points = load_calibration_points()
        calibration = load_calibration()

        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        cap = open_camera(calibration)

        print("12개 표본 affine XY 보정을 적용합니다.")
        print(
            f"상공 z={APPROACH_Z_M:.4f}, 집기 z={GRASP_Z_M:.4f}, "
            f"시험 상승 z={LIFT_Z_M:.4f} m"
        )
        print("이 프로그램은 호박 하나만 시험하며 자동 적재하지 않습니다.")

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = np.asarray(calibration["camera_joints"], dtype=float)
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)
        safe_return_allowed = True

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
        safe_return_allowed = False
        arm.move_joints(view_joints, duration=MOVE_DURATION_SEC)
        safe_return_allowed = True
        time.sleep(SETTLE_TIME_SEC)

        target = detect_exactly_one(model, cap, calibration, offset_deg)
        if target is None:
            return

        raw_xy = np.asarray([target.x, target.y], dtype=float)
        inside, hull_distance = inside_calibrated_region(raw_xy, calibration_points)
        corrected_xy = apply_affine(raw_xy)

        print("\n========== 좌표 확인 ==========")
        print(f"YOLO 원본: x={raw_xy[0]:.4f}, y={raw_xy[1]:.4f} m")
        print(
            f"보정 좌표: x={corrected_xy[0]:.4f}, "
            f"y={corrected_xy[1]:.4f} m"
        )
        print(
            f"보정 이동량: dx={(corrected_xy[0] - raw_xy[0]) * 1000:+.1f} mm, "
            f"dy={(corrected_xy[1] - raw_xy[1]) * 1000:+.1f} mm"
        )
        print(f"표본 영역 경계 거리: {hull_distance * 1000:+.1f} mm")
        print("===============================")
        if not inside:
            print("[이동 금지] 검출 좌표가 보정 표본 영역 밖에 있습니다.")
            return

        cap.release()
        cap = None
        cv2.destroyAllWindows()

        print("IK 계산 전에 중앙 카메라 자세로 돌아갑니다.")
        safe_return_allowed = False
        arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
        safe_return_allowed = True
        time.sleep(SETTLE_TIME_SEC)

        current_joints = np.asarray(arm.joints(), dtype=float)
        plan = find_complete_plan(
            arm,
            float(corrected_xy[0]),
            float(corrected_xy[1]),
            current_joints,
        )
        if plan is None:
            print("[이동 금지] 전 구간을 안전하게 잇는 동일 pitch IK가 없습니다.")
            return

        print("\n========== 단일 집기 계획 ==========")
        print(f"XY [m]: {np.round(corrected_xy, 4)}")
        print(f"선택 pitch: {plan['pitch_deg']:.1f}도 (전 구간 고정)")
        print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
        print(f"상공 관절 [deg]: {np.round(np.degrees(plan['approach']), 1)}")
        print(f"집기 관절 [deg]: {np.round(np.degrees(plan['grasp']), 1)}")
        print(f"상승 관절 [deg]: {np.round(np.degrees(plan['lift']), 1)}")
        print(f"상공 변화 [deg]: {np.round(plan['approach_delta'], 1)}")
        print(f"하강 변화 [deg]: {np.round(plan['descent_delta'], 1)}")
        print(f"상승 변화 [deg]: {np.round(plan['lift_delta'], 1)}")
        print("그리퍼: 0.0 방향으로 닫고 전류 제한 감지 시 밀기 중단")
        print("자동 적재 없음 / 확인어 없이는 다음 단계 진행 안 함")
        print("=====================================")

        if not require_exact(
            "사람·케이블을 치우고 시험을 시작하려면 START 입력: ",
            "START",
        ):
            return

        print("그리퍼를 작업 폭으로 엽니다.")
        arm.open_gripper(duration=GRIPPER_DURATION_SEC, stall_guard=True)

        print(f"{APPROACH_DURATION_SEC:.1f}초 동안 호박 상공으로 이동합니다.")
        safe_return_allowed = False
        arm.move_joints(plan["approach"], duration=APPROACH_DURATION_SEC)
        safe_return_allowed = True
        retreat_joints = plan["approach"]

        if not require_exact(
            "중심과 주변 넝쿨을 확인하고 하강하려면 DESCEND 입력: ",
            "DESCEND",
        ):
            return

        print(f"{DESCEND_DURATION_SEC:.1f}초 동안 z={GRASP_Z_M:.4f} m로 하강합니다.")
        safe_return_allowed = False
        arm.move_joints(plan["grasp"], duration=DESCEND_DURATION_SEC)
        safe_return_allowed = True
        retreat_needed = True

        if not require_exact(
            "손가락이 넝쿨 위·호박 옆면에 있는지 확인 후 GRIP 입력: ",
            "GRIP",
        ):
            return

        print("전류 제한을 사용해 천천히 닫습니다.")
        arm.gripper(
            0.0,
            duration=GRIPPER_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        holding = True

        if not require_exact(
            "호박이 안정적으로 잡혔으면 LIFT 입력(아니면 Enter로 중단): ",
            "LIFT",
        ):
            return

        print(f"{LIFT_DURATION_SEC:.1f}초 동안 3 cm 들어 올립니다.")
        safe_return_allowed = False
        arm.move_joints(plan["lift"], duration=LIFT_DURATION_SEC)
        safe_return_allowed = True

        input("집기 상태를 확인했습니다. 내려놓으려면 Enter: ")
        print("같은 경로로 집기 높이까지 내립니다.")
        safe_return_allowed = False
        arm.move_joints(plan["grasp"], duration=LOWER_DURATION_SEC)
        safe_return_allowed = True

        print("그리퍼를 열어 호박을 내려놓습니다.")
        arm.open_gripper(duration=GRIPPER_DURATION_SEC, stall_guard=True)
        holding = False
        time.sleep(0.5)

        print("상공 자세로 빠져나옵니다.")
        safe_return_allowed = False
        arm.move_joints(plan["approach"], duration=LIFT_DURATION_SEC)
        safe_return_allowed = True
        retreat_needed = False

        print("중앙 카메라 자세로 복귀합니다.")
        safe_return_allowed = False
        arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
        safe_return_allowed = True
        print("단일 집기 테스트가 끝났습니다.")

    except KeyboardInterrupt:
        safe_return_allowed = False
        print("\n사용자가 테스트를 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if holding:
                    print(
                        "경고: 그리퍼가 닫힌 상태입니다. 호박과 팔을 받친 뒤 "
                        "Enter를 누르면 그리퍼를 엽니다."
                    )
                    try:
                        input()
                        arm.open_gripper(
                            duration=GRIPPER_DURATION_SEC,
                            stall_guard=True,
                        )
                        holding = False
                    except (EOFError, KeyboardInterrupt, Exception) as error:
                        print(f"자동 열기 생략: {error}")

                if (
                    safe_return_allowed
                    and not holding
                    and retreat_needed
                    and retreat_joints is not None
                ):
                    print("낮은 위치에서 상공 자세로 먼저 빠져나옵니다.")
                    arm.move_joints(retreat_joints, duration=LIFT_DURATION_SEC)
                    retreat_needed = False

                if safe_return_allowed and not holding and calibration is not None:
                    print("중앙 카메라 자세로 돌아갑니다.")
                    arm.move_joints(
                        np.asarray(calibration["camera_joints"], dtype=float),
                        duration=RETURN_DURATION_SEC,
                    )
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
