"""Safely test an affine-corrected pumpkin XY target from above.

The program detects exactly one pumpkin, applies the saved XY correction,
pre-computes several inverse-kinematics candidates, and selects the candidate
with the smallest joint change.  Motion requires the exact confirmation MOVE.
It never descends to grasp height and never opens or closes the gripper.
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
PLANE_CALIBRATION_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")

ALLOWED_OFFSETS_DEG = (-140, -110, -80, -50, -20, 0, 10, 40, 70, 100, 130, 140)
PITCH_CANDIDATES_DEG = (85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35)

# This is a high observation point, not a grasp point.
HEIGHT_ABOVE_GRASP_M = 0.08
MIN_APPROACH_Z_M = 0.06
APPROACH_DURATION_SEC = 12.0
RETURN_DURATION_SEC = 12.0

# Reject a mathematically valid IK solution if it requires a large posture jump.
MAX_SINGLE_JOINT_CHANGE_DEG = 65.0
MAX_TOTAL_JOINT_CHANGE_DEG = 170.0
CALIBRATION_HULL_MARGIN_M = 0.005


def load_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"필요한 파일이 없습니다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_correction():
    data = load_json(CORRECTION_PATH)
    samples = data.get("samples", [])
    correction = data.get("correction", {})

    if len(samples) < 3:
        raise ValueError("XY 보정 표본이 3개보다 적습니다.")
    if correction.get("type") != "affine":
        raise ValueError("affine XY 보정 결과가 없습니다.")

    matrix = np.asarray(correction["matrix"], dtype=float)
    bias = np.asarray(correction["bias_m"], dtype=float)
    if matrix.shape != (2, 2) or bias.shape != (2,):
        raise ValueError("XY 보정 행렬 또는 bias 형식이 올바르지 않습니다.")
    if not np.all(np.isfinite(matrix)) or not np.all(np.isfinite(bias)):
        raise ValueError("XY 보정값에 유효하지 않은 수가 있습니다.")

    predicted_points = np.asarray(
        [sample["predicted_xy_m"] for sample in samples],
        dtype=np.float32,
    )
    return matrix, bias, predicted_points, correction


def load_safe_z():
    data = load_json(PLANE_CALIBRATION_PATH)
    grasp = data.get("grasp", {})
    grasp_z = float(grasp["grasp_z_m"])
    safe_z = max(MIN_APPROACH_Z_M, grasp_z + HEIGHT_ABOVE_GRASP_M)
    if not math.isfinite(safe_z):
        raise ValueError("안전 접근 높이가 올바르지 않습니다.")
    return grasp_z, safe_z


def inside_calibrated_region(point_xy, calibration_points):
    hull = cv2.convexHull(calibration_points.reshape(-1, 1, 2))
    signed_distance = cv2.pointPolygonTest(
        hull,
        (float(point_xy[0]), float(point_xy[1])),
        True,
    )
    return signed_distance >= -CALIBRATION_HULL_MARGIN_M, float(signed_distance)


def apply_affine(point_xy, matrix, bias):
    return matrix @ np.asarray(point_xy, dtype=float) + bias


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


def find_safest_ik(arm, xyz, current_joints):
    """Find a reachable explicit-pitch solution nearest to current joints."""
    kinematics = get_kinematics(arm)
    candidates = []
    failures = []

    for pitch_deg in PITCH_CANDIDATES_DEG:
        try:
            target_joints = np.asarray(
                kinematics.inverse(
                    tuple(float(value) for value in xyz),
                    current_joints,
                    pitch=np.radians(pitch_deg),
                    roll=0.0,
                ),
                dtype=float,
            )
        except (ValueError, RuntimeError) as error:
            failures.append((pitch_deg, str(error)))
            continue

        if target_joints.shape != current_joints.shape:
            failures.append((pitch_deg, "관절 배열 크기 불일치"))
            continue
        if not np.all(np.isfinite(target_joints)):
            failures.append((pitch_deg, "유효하지 않은 관절값"))
            continue

        delta_deg = np.abs(np.degrees(target_joints - current_joints))
        max_delta = float(np.max(delta_deg))
        total_delta = float(np.sum(delta_deg))
        if max_delta > MAX_SINGLE_JOINT_CHANGE_DEG:
            failures.append((pitch_deg, f"단일 관절 변화 {max_delta:.1f}도"))
            continue
        if total_delta > MAX_TOTAL_JOINT_CHANGE_DEG:
            failures.append((pitch_deg, f"전체 관절 변화 {total_delta:.1f}도"))
            continue

        score = max_delta + 0.15 * total_delta
        candidates.append(
            {
                "pitch_deg": float(pitch_deg),
                "joints": target_joints,
                "delta_deg": delta_deg,
                "max_delta_deg": max_delta,
                "total_delta_deg": total_delta,
                "score": score,
            }
        )

    if not candidates:
        print("\n[IK 실패 내역]")
        for pitch_deg, reason in failures:
            print(f"  pitch={pitch_deg:>2}도: {reason}")
        return None

    return min(candidates, key=lambda candidate: candidate["score"])


def main():
    arm = None
    cap = None
    calibration = None
    safe_return_allowed = False

    try:
        matrix, bias, calibration_points, correction = load_correction()
        grasp_z, safe_z = load_safe_z()
        calibration = load_calibration()

        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        cap = open_camera(calibration)

        print(
            f"XY 보정 표본={correction['sample_count']}개, "
            f"RMS={correction['rms_residual_mm']:.1f} mm, "
            f"최대={correction['max_residual_mm']:.1f} mm"
        )
        print(f"집기 z={grasp_z:.4f} m, 이번 테스트 접근 z={safe_z:.4f} m")
        print("이 프로그램은 하강하거나 그리퍼를 작동하지 않습니다.")

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
        corrected_xy = apply_affine(raw_xy, matrix, bias)

        print("\n========== 좌표 확인 ==========")
        print(f"YOLO 원본: x={raw_xy[0]:.4f}, y={raw_xy[1]:.4f} m")
        print(
            f"보정 좌표: x={corrected_xy[0]:.4f}, "
            f"y={corrected_xy[1]:.4f} m"
        )
        print(
            "보정 이동량: "
            f"dx={(corrected_xy[0] - raw_xy[0]) * 1000.0:+.1f} mm, "
            f"dy={(corrected_xy[1] - raw_xy[1]) * 1000.0:+.1f} mm"
        )
        print(f"보정 표본 영역 경계 거리: {hull_distance * 1000.0:+.1f} mm")
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
        target_xyz = np.asarray(
            [corrected_xy[0], corrected_xy[1], safe_z],
            dtype=float,
        )
        solution = find_safest_ik(arm, target_xyz, current_joints)
        if solution is None:
            print("[이동 금지] 안전 기준을 만족하는 IK 자세가 없습니다.")
            return

        print("\n========== 이동 계획 ==========")
        print(f"목표 XYZ [m]: {np.round(target_xyz, 4)}")
        print(f"선택 pitch: {solution['pitch_deg']:.1f}도")
        print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
        print(f"목표 관절 [deg]: {np.round(np.degrees(solution['joints']), 1)}")
        print(f"관절 변화 [deg]: {np.round(solution['delta_deg'], 1)}")
        print(f"최대 변화: {solution['max_delta_deg']:.1f}도")
        print("하강 없음 / 그리퍼 동작 없음")
        print("===============================")

        confirmation = input(
            "사람·케이블을 치우고 위 계획대로 상공 접근하려면 MOVE 입력: "
        ).strip()
        if confirmation != "MOVE":
            print("접근 테스트를 취소했습니다.")
            return

        print(f"{APPROACH_DURATION_SEC:.1f}초 동안 상공 접근 자세로 이동합니다.")
        safe_return_allowed = False
        arm.move_joints(
            solution["joints"],
            duration=APPROACH_DURATION_SEC,
        )
        safe_return_allowed = True
        print("접근 완료. 그리퍼 중심이 호박 중심 위인지 눈으로 확인하세요.")
        input("확인이 끝나면 Enter를 눌러 중앙 자세로 복귀: ")

        safe_return_allowed = False
        arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
        safe_return_allowed = True
        time.sleep(SETTLE_TIME_SEC)
        print("접근 테스트가 끝났습니다.")

    except KeyboardInterrupt:
        safe_return_allowed = False
        print("\n사용자가 테스트를 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if safe_return_allowed and calibration is not None:
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
