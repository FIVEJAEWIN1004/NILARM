#!/usr/bin/env python3
"""Teach one real pumpkin grasp pose without closing the gripper.

This stage runs only after the 9-point plane calibration has passed visual XY
validation.  The operator places one pumpkin near marker 5, opens the gripper,
and manually teaches a comfortable grasp height and pitch.  The script saves a
separate grasp-pose JSON; it never modifies the plane calibration JSON and it
never closes the gripper on the pumpkin.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


PLANE_CALIBRATION_PATH = Path(__file__).with_name(
    "pumpkin_plane_calibration.json"
)
OUTPUT_PATH = Path(__file__).with_name("pumpkin_grasp_pose_calibration.json")

GRIPPER_OPEN_DURATION_SEC = 3.0
APPROACH_CLEARANCE_M = 0.080
# This is a robot-model z offset, not a literal physical air gap.  The taught
# TCP and the real plastic contact point differ with pitch, and the validated
# floor-plane residual is about +/-6 mm.  A small negative value is therefore
# valid when the real gripper is visibly above the table.
MIN_GRASP_CLEARANCE_M = -0.020
MAX_GRASP_CLEARANCE_M = 0.060


class CalibrationCancelled(Exception):
    """Raised when the user cancels without saving."""


def checked_array(value, shape, name):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} 형식이 올바르지 않습니다: {array.shape}")
    return array


def load_plane_calibration() -> dict:
    if not PLANE_CALIBRATION_PATH.is_file():
        raise FileNotFoundError(
            f"9점 평면 보정 파일이 없습니다: {PLANE_CALIBRATION_PATH}"
        )

    data = json.loads(PLANE_CALIBRATION_PATH.read_text(encoding="utf-8"))
    if data.get("method") != "9_point_ground_plane_homography":
        raise ValueError("현재 파일은 검증된 9점 평면 보정 형식이 아닙니다.")

    quality = data.get("quality", {})
    rms_mm = float(quality["rms_error_mm"])
    max_mm = float(quality["max_error_mm"])
    floor_rms_mm = float(quality["floor_plane_rms_error_mm"])
    floor_max_mm = float(quality["floor_plane_max_error_mm"])
    if rms_mm > 8.0 or max_mm > 15.0:
        raise ValueError(
            f"평면 XY 품질이 기준 밖입니다: RMS={rms_mm:.1f}, "
            f"최대={max_mm:.1f} mm"
        )
    if floor_rms_mm > 5.0 or floor_max_mm > 8.0:
        raise ValueError(
            f"바닥 평면 품질이 기준 밖입니다: RMS={floor_rms_mm:.1f}, "
            f"최대={floor_max_mm:.1f} mm"
        )

    return {
        "robot_points_xy": checked_array(
            data["robot_points_xy_m"], (9, 2), "robot_points_xy_m"
        ),
        "floor_coefficients": checked_array(
            quality["floor_plane_z_from_xy"], (3,), "floor plane"
        ),
        "plane_quality": {
            "rms_error_mm": rms_mm,
            "max_error_mm": max_mm,
            "floor_rms_error_mm": floor_rms_mm,
            "floor_max_error_mm": floor_max_mm,
        },
    }


def floor_z_at(x: float, y: float, coefficients: np.ndarray) -> float:
    a, b, c = coefficients
    value = float(a * x + b * y + c)
    if not np.isfinite(value):
        raise ValueError("바닥 평면 z 계산 결과가 올바르지 않습니다.")
    return value


def inside_robot_region(xy: np.ndarray, points: np.ndarray) -> tuple[bool, float]:
    hull = cv2.convexHull(points.astype(np.float32).reshape(-1, 1, 2))
    distance = float(
        cv2.pointPolygonTest(hull, (float(xy[0]), float(xy[1])), True)
    )
    return distance >= 0.0, distance


def read_tool_rpy(arm: OmxFollower) -> np.ndarray:
    if not hasattr(arm, "tool_rpy"):
        raise RuntimeError(
            "현재 omx_f에 arm.tool_rpy()가 없어 pitch를 읽을 수 없습니다."
        )
    rpy = np.asarray(arm.tool_rpy(), dtype=float)
    if rpy.shape != (3,) or not np.all(np.isfinite(rpy)):
        raise RuntimeError(f"그리퍼 자세 RPY를 읽지 못했습니다: {rpy}")
    return rpy


def save_result(result: dict) -> None:
    temporary = OUTPUT_PATH.with_name(OUTPUT_PATH.name + ".tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(OUTPUT_PATH)


def main() -> None:
    arm = None
    pumpkin_removed = False
    saved = False

    try:
        plane = load_plane_calibration()
        q = plane["plane_quality"]
        print(
            f"검증된 평면 사용: XY RMS={q['rms_error_mm']:.2f} mm, "
            f"최대={q['max_error_mm']:.2f} mm"
        )
        print("이 프로그램은 그리퍼를 열기만 하며, 호박을 닫아 잡지 않습니다.")
        print("평면 보정 JSON은 수정하지 않고 별도의 집기 자세 파일을 저장합니다.")

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        confirmation = input(
            "그리퍼 주변이 비어 있습니다. 작업용 폭으로 열려면 OPEN 입력: "
        ).strip()
        if confirmation != "OPEN":
            raise CalibrationCancelled
        arm.open_gripper(duration=GRIPPER_OPEN_DURATION_SEC, stall_guard=True)

        print("\n호박 한 개를 5번 스티커 중심에 놓으세요.")
        print("목표는 열린 두 손가락이 호박 양옆을 감쌀 수 있는 높이와 방향입니다.")
        input("호박을 놓고 팔을 양손으로 받친 상태에서 Enter: ")

        with arm.teach():
            print("토크가 풀렸습니다. 팔을 계속 양손으로 받치세요.")
            print("열린 그리퍼 중심을 호박 중심에 맞추되 호박을 누르지 마세요.")
            input("원하는 실제 집기 높이와 방향에 맞춘 뒤 Enter: ")
            pose = np.asarray(arm.pose(), dtype=float).copy()
            joints = np.asarray(arm.joints(), dtype=float).copy()
            tool_rpy = read_tool_rpy(arm)

        if pose.size < 3 or not np.all(np.isfinite(pose[:3])):
            raise RuntimeError("집기 자세의 XYZ를 읽지 못했습니다.")
        if joints.shape != (5,) or not np.all(np.isfinite(joints)):
            raise RuntimeError("집기 자세의 관절각을 읽지 못했습니다.")

        xy = pose[:2]
        inside, hull_margin_m = inside_robot_region(
            xy, plane["robot_points_xy"]
        )
        if not inside:
            raise ValueError(
                "집기 자세가 9점 보정 영역 밖입니다: "
                f"경계 거리 {hull_margin_m * 1000:.1f} mm"
            )

        floor_z = floor_z_at(
            float(xy[0]), float(xy[1]), plane["floor_coefficients"]
        )
        grasp_z = float(pose[2])
        grasp_clearance_m = grasp_z - floor_z
        if not MIN_GRASP_CLEARANCE_M <= grasp_clearance_m <= MAX_GRASP_CLEARANCE_M:
            raise ValueError(
                "기록된 집기 z 오프셋이 허용 범위를 벗어납니다: "
                f"로봇 모델 기준 {grasp_clearance_m * 1000:.1f} mm "
                f"(허용 {MIN_GRASP_CLEARANCE_M * 1000:.0f}~"
                f"{MAX_GRASP_CLEARANCE_M * 1000:.0f} mm)"
            )

        roll_rad, pitch_rad, yaw_rad = [float(value) for value in tool_rpy]
        result = {
            "schema_version": 1,
            "method": "manual_open_gripper_grasp_pose",
            "saved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_plane_calibration": PLANE_CALIBRATION_PATH.name,
            "taught_pose_m": pose.tolist(),
            "taught_xy_m": [float(xy[0]), float(xy[1])],
            "taught_joints_rad": joints.tolist(),
            "taught_joints_deg": np.degrees(joints).tolist(),
            "tool_rpy_rad": [roll_rad, pitch_rad, yaw_rad],
            "tool_rpy_deg": np.degrees(tool_rpy).tolist(),
            "tool_pitch_rad": pitch_rad,
            "tool_pitch_deg": float(np.degrees(pitch_rad)),
            "floor_z_m": floor_z,
            "grasp_z_m": grasp_z,
            "model_relative_grasp_z_offset_m": grasp_clearance_m,
            "model_relative_grasp_z_offset_mm": grasp_clearance_m * 1000.0,
            "grasp_clearance_above_floor_m": grasp_clearance_m,
            "grasp_clearance_above_floor_mm": grasp_clearance_m * 1000.0,
            "approach_clearance_m": APPROACH_CLEARANCE_M,
            "approach_z_at_taught_xy_m": grasp_z + APPROACH_CLEARANCE_M,
            "calibration_region_margin_m": hull_margin_m,
            "plane_quality": q,
        }

        print("\n========== 집기 자세 측정 결과 ==========")
        print(f"XYZ [m]: {np.round(pose[:3], 4)}")
        print(f"관절 [deg]: {np.round(np.degrees(joints), 1)}")
        print(f"tool RPY [deg]: {np.round(np.degrees(tool_rpy), 1)}")
        print(f"계산 바닥 z: {floor_z:.4f} m")
        print(
            "로봇 모델 기준 집기 z 오프셋: "
            f"{grasp_clearance_m * 1000:.1f} mm"
        )
        print("주의: 이 값은 실제 물리적 틈새 높이가 아닙니다.")
        print(f"보정 영역 경계 여유: {hull_margin_m * 1000:.1f} mm")
        print("그리퍼는 닫히지 않았습니다.")
        print("=========================================")

        confirmation = input(
            "결과를 별도 파일에 저장하려면 SAVE / 취소하려면 Q: "
        ).strip()
        if confirmation != "SAVE":
            raise CalibrationCancelled

        save_result(result)
        saved = True
        print("집기 자세를 저장했습니다:", OUTPUT_PATH)

        input("호박을 치우고 팔 주변을 비운 뒤 Enter: ")
        pumpkin_removed = True

    except CalibrationCancelled:
        print("집기 자세를 저장하지 않았습니다.")
        if arm is not None:
            input("호박과 장애물을 치운 뒤 Enter: ")
            pumpkin_removed = True
    except KeyboardInterrupt:
        print("\n사용자가 중단했습니다. 자동 정리 자세를 생략합니다.")
    finally:
        cv2.destroyAllWindows()
        if arm is not None:
            try:
                if pumpkin_removed:
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "호박 제거가 확인되지 않아 자동 정리 자세를 생략합니다. "
                        "팔을 받치고 주변을 확인하세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")

        if saved:
            print("다음 단계에서는 이 자세로 접근만 시험하고 아직 호박을 잡지 않습니다.")


if __name__ == "__main__":
    main()
