#!/usr/bin/env python3
"""Validate one YOLO-detected pumpkin target without closing the gripper.

This stage uses both saved calibration files:

* pumpkin_plane_calibration.json: camera pose, 9-point homography, floor plane
* pumpkin_grasp_pose_calibration.json: taught grasp pitch and model-relative z

Exactly one stable pumpkin must be visible in the central calibration view.
After the operator locks the target with M, the arm approaches in three
confirmed stages: 80, 50, and 30 mm above the planned grasp pose.  The
program never commands the gripper and never reaches the final grasp pose.
"""

from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from vision_pkg.pumpkin_detection import yolo_detector


PLANE_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")
GRASP_PATH = Path(__file__).with_name("pumpkin_grasp_pose_calibration.json")

from .runtime_paths import vision_model_candidates

MODEL_CANDIDATES = vision_model_candidates()

# Verified arm camera. Never fall back to the laptop camera at /dev/video0.
CAMERA_DEVICE_PATH = Path("/dev/video2")
CAMERA_EXPECTED_NAME = "Innomaker"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

CONFIDENCE = 0.70
YOLO_IMAGE_SIZE = 416
TARGET_CLASS_NAMES = set(yolo_detector.DEFAULT_TARGET_CLASS_NAMES)
STABLE_SAMPLE_COUNT = 10
MAX_PIXEL_SPREAD = 8.0

# The user requested the centre of the YOLO detection box for this validation.
# Keep this explicit because a later experiment may compare another anchor.
TARGET_PIXEL_MODE = "box_center"

# Visual validation at the central camera pose showed that the box-centre
# target stopped about 10 mm toward the robot base.  In the OMX base frame,
# moving away from the base is +X.  Keep this runtime correction separate
# from the 9-point plane calibration; scanning views will later rotate an
# equivalent correction with joint1 instead of blindly reusing +X.
TARGET_X_OFFSET_M = 0.010
TARGET_Y_OFFSET_M = 0.000

# Kept separate from both calibration JSON files so it can be tuned later.
VINE_AVOIDANCE_Z_OFFSET_M = 0.010
APPROACH_CLEARANCES_M = (0.080, 0.050, 0.030)

CAMERA_MOVE_DURATION_SEC = 6.0
HIGH_MOVE_DURATION_SEC = 12.0
LOWER_MOVE_DURATION_SEC = 8.0
RETURN_DURATION_SEC = 12.0
SETTLE_TIME_SEC = 1.0

MAX_HIGH_SINGLE_JOINT_CHANGE_DEG = 65.0
MAX_HIGH_TOTAL_JOINT_CHANGE_DEG = 170.0
MAX_LOWER_SINGLE_JOINT_CHANGE_DEG = 25.0
MAX_LOWER_TOTAL_JOINT_CHANGE_DEG = 65.0

MAX_SAVED_XY_RMS_MM = 8.0
MAX_SAVED_XY_ERROR_MM = 15.0
MAX_SAVED_FLOOR_RMS_MM = 5.0
MAX_SAVED_FLOOR_ERROR_MM = 8.0


class UserCancelled(Exception):
    """Raised when the user cancels before target motion."""


def checked_array(value, shape, name):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} 형식이 올바르지 않습니다: {array.shape}")
    return array


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"필요한 파일이 없습니다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_calibrations() -> dict:
    plane = load_json(PLANE_PATH)
    grasp = load_json(GRASP_PATH)

    if plane.get("method") != "9_point_ground_plane_homography":
        raise ValueError("검증된 9점 평면 보정 파일이 아닙니다.")
    if grasp.get("method") != "manual_open_gripper_grasp_pose":
        raise ValueError("수동 집기 자세 보정 파일 형식이 아닙니다.")

    quality = plane.get("quality", {})
    xy_rms = float(quality["rms_error_mm"])
    xy_max = float(quality["max_error_mm"])
    floor_rms = float(quality["floor_plane_rms_error_mm"])
    floor_max = float(quality["floor_plane_max_error_mm"])
    if xy_rms > MAX_SAVED_XY_RMS_MM or xy_max > MAX_SAVED_XY_ERROR_MM:
        raise ValueError(
            f"저장된 XY 품질이 기준 밖입니다: RMS={xy_rms:.1f} mm, "
            f"최대={xy_max:.1f} mm"
        )
    if floor_rms > MAX_SAVED_FLOOR_RMS_MM or floor_max > MAX_SAVED_FLOOR_ERROR_MM:
        raise ValueError(
            f"저장된 바닥 품질이 기준 밖입니다: RMS={floor_rms:.1f} mm, "
            f"최대={floor_max:.1f} mm"
        )

    pitch = float(grasp["tool_pitch_rad"])
    tool_rpy = checked_array(grasp["tool_rpy_rad"], (3,), "tool_rpy_rad")
    grasp_offset = float(grasp["model_relative_grasp_z_offset_m"])
    if not np.isfinite(pitch) or not np.isfinite(grasp_offset):
        raise ValueError("저장된 집기 각도 또는 z 오프셋이 올바르지 않습니다.")

    return {
        "camera_joints": checked_array(
            plane["camera_pose"]["joints_rad"], (5,), "camera_pose.joints_rad"
        ),
        "image_points": checked_array(
            plane["image_points_px"], (9, 2), "image_points_px"
        ),
        "robot_points": checked_array(
            plane["robot_points_xy_m"], (9, 2), "robot_points_xy_m"
        ),
        "homography": checked_array(
            plane["homography_px_to_robot_xy"], (3, 3), "homography"
        ),
        "floor_coefficients": checked_array(
            quality["floor_plane_z_from_xy"], (3,), "floor plane"
        ),
        "pitch_rad": pitch,
        "roll_rad": float(tool_rpy[0]),
        "grasp_offset_m": grasp_offset,
        "quality": (xy_rms, xy_max, floor_rms, floor_max),
    }


def find_model_path() -> Path:
    for path in MODEL_CANDIDATES:
        if path.is_file():
            return path
    attempted = "\n".join(f"- {path}" for path in MODEL_CANDIDATES)
    raise FileNotFoundError(f"YOLO 모델을 찾지 못했습니다:\n{attempted}")


def normalize_name(value) -> str:
    """Compatibility wrapper for older harvest modules."""
    return yolo_detector.normalize_name(value)


def validate_model(model: YOLO) -> None:
    """Compatibility wrapper for older harvest modules."""
    yolo_detector.validate_model(model, TARGET_CLASS_NAMES)


def verified_camera_source() -> str:
    if not CAMERA_DEVICE_PATH.exists():
        raise RuntimeError(f"팔 카메라 장치가 없습니다: {CAMERA_DEVICE_PATH}")
    name_path = Path(f"/sys/class/video4linux/{CAMERA_DEVICE_PATH.name}/name")
    if not name_path.is_file():
        raise RuntimeError(f"카메라 이름을 확인할 수 없습니다: {name_path}")
    device_name = name_path.read_text(encoding="utf-8").strip()
    if CAMERA_EXPECTED_NAME.lower() not in device_name.lower():
        raise RuntimeError(
            f"{CAMERA_DEVICE_PATH}는 팔 카메라가 아닙니다: {device_name}\n"
            "노트북 카메라로는 실행하지 않습니다."
        )
    print(f"팔 카메라 확인: {CAMERA_DEVICE_PATH} ({device_name})")
    return str(CAMERA_DEVICE_PATH)


def open_camera() -> cv2.VideoCapture:
    cap = cv2.VideoCapture(verified_camera_source(), cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"팔 카메라를 열 수 없습니다: {CAMERA_DEVICE_PATH}")
    for _ in range(8):
        cap.read()
    return cap


def inside_hull(point, points: np.ndarray) -> tuple[bool, float]:
    hull = cv2.convexHull(points.astype(np.float32).reshape(-1, 1, 2))
    distance = float(
        cv2.pointPolygonTest(hull, (float(point[0]), float(point[1])), True)
    )
    return distance >= 0.0, distance


def pixel_to_robot_xy(u: float, v: float, homography: np.ndarray) -> np.ndarray:
    pixel = np.asarray([[[u, v]]], dtype=np.float32)
    xy = cv2.perspectiveTransform(pixel, homography).reshape(2).astype(float)
    if not np.all(np.isfinite(xy)):
        raise ValueError("호박 픽셀을 로봇 XY로 변환하지 못했습니다.")
    return xy


def floor_z_at(x: float, y: float, coefficients: np.ndarray) -> float:
    a, b, c = coefficients
    value = float(a * x + b * y + c)
    if not np.isfinite(value):
        raise ValueError("바닥 평면 z 계산 결과가 올바르지 않습니다.")
    return value


def detect_valid_boxes(model: YOLO, frame: np.ndarray, image_points: np.ndarray):
    result, pumpkin_boxes = yolo_detector.detect_pumpkin_boxes(
        model,
        frame,
        confidence=CONFIDENCE,
        image_size=YOLO_IMAGE_SIZE,
        target_names=TARGET_CLASS_NAMES,
    )
    detections = []
    for box in pumpkin_boxes:
        u, v = box.center
        inside, margin_px = inside_hull((u, v), image_points)
        if not inside:
            continue
        detections.append(
            {
                "u": u,
                "v": v,
                "confidence": box.confidence,
                "margin_px": margin_px,
            }
        )
    return result, detections


def stable_pixel(history) -> tuple[float, float] | None:
    if len(history) < STABLE_SAMPLE_COUNT:
        return None
    points = np.asarray([[item["u"], item["v"]] for item in history], dtype=float)
    median = np.median(points, axis=0)
    spread = float(np.max(np.linalg.norm(points - median, axis=1)))
    if spread > MAX_PIXEL_SPREAD:
        return None
    return float(median[0]), float(median[1])


def choose_pumpkin(model: YOLO, cap, calibration) -> tuple[float, float] | None:
    window = "One pumpkin - M lock target / Q cancel"
    history = deque(maxlen=STABLE_SAMPLE_COUNT)
    boundary = cv2.convexHull(
        calibration["image_points"].astype(np.int32).reshape(-1, 1, 2)
    )
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    print("\n청록색 보정 영역 안에 호박 하나만 놓으세요.")
    print("STABLE이 표시되면 M을 누르세요. 취소는 Q입니다.")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("팔 카메라 프레임을 읽지 못했습니다.")
        cv2.imwrite("green_test.jpg", frame)
        if frame.shape[:2] != (CAMERA_HEIGHT, CAMERA_WIDTH):
            raise RuntimeError(
                f"영상 크기가 {frame.shape[1]}x{frame.shape[0]}입니다. "
                f"필요한 크기는 {CAMERA_WIDTH}x{CAMERA_HEIGHT}입니다."
            )

        result, detections = detect_valid_boxes(
            model, frame, calibration["image_points"]
        )
        annotated = result.plot()
        cv2.polylines(annotated, [boundary], True, (255, 255, 0), 2)

        if len(detections) != 1:
            history.clear()
            status = f"Need exactly 1 valid pumpkin (now {len(detections)})"
            color = (0, 0, 255)
        else:
            detection = detections[0]
            history.append(detection)
            point = (int(round(detection["u"])), int(round(detection["v"])))
            cv2.drawMarker(
                annotated, point, (0, 0, 255), cv2.MARKER_CROSS, 24, 2
            )
            selected = stable_pixel(history)
            if selected is None:
                status = f"Stabilizing {len(history)}/{STABLE_SAMPLE_COUNT}"
                color = (0, 165, 255)
            else:
                status = "STABLE - Press M"
                color = (0, 255, 0)

        cv2.putText(
            annotated, status, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.70, color, 2
        )
        cv2.putText(
            annotated,
            "Red cross = YOLO box center",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
        cv2.imshow(window, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            return None
        if key in (ord("m"), ord("M")):
            selected = stable_pixel(history)
            if selected is not None:
                return selected
            print("아직 호박 중심 좌표가 안정되지 않았습니다.")
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            return None


def get_kinematics(arm):
    kinematics = getattr(arm, "kin", None)
    if kinematics is None:
        kinematics = getattr(arm, "_kin", None)
    if kinematics is None or not hasattr(kinematics, "inverse"):
        raise RuntimeError("OmxFollower에서 inverse kinematics를 찾지 못했습니다.")
    return kinematics


def plan_fixed_pose_stages(arm, xyz_stages, current_joints, pitch_rad, roll_rad):
    kinematics = get_kinematics(arm)
    joints_stages = []
    deltas = []
    seed = current_joints

    for index, xyz in enumerate(xyz_stages):
        target = np.asarray(
            kinematics.inverse(
                tuple(float(value) for value in xyz),
                seed,
                pitch=float(pitch_rad),
                roll=float(roll_rad),
            ),
            dtype=float,
        )
        if target.shape != current_joints.shape or not np.all(np.isfinite(target)):
            raise ValueError(f"단계 {index + 1} IK 결과가 올바르지 않습니다.")

        delta_deg = np.abs(np.degrees(target - seed))
        max_delta = float(np.max(delta_deg))
        total_delta = float(np.sum(delta_deg))
        if index == 0:
            if max_delta > MAX_HIGH_SINGLE_JOINT_CHANGE_DEG:
                raise ValueError(f"80mm 접근 단일 관절 변화 {max_delta:.1f}도")
            if total_delta > MAX_HIGH_TOTAL_JOINT_CHANGE_DEG:
                raise ValueError(f"80mm 접근 전체 관절 변화 {total_delta:.1f}도")
        else:
            if max_delta > MAX_LOWER_SINGLE_JOINT_CHANGE_DEG:
                raise ValueError(f"하강 단일 관절 변화 {max_delta:.1f}도")
            if total_delta > MAX_LOWER_TOTAL_JOINT_CHANGE_DEG:
                raise ValueError(f"하강 전체 관절 변화 {total_delta:.1f}도")

        joints_stages.append(target)
        deltas.append((delta_deg, max_delta, total_delta))
        seed = target
    return joints_stages, deltas


def main() -> None:
    arm = None
    cap = None
    calibration = None
    safe_to_park = False

    try:
        calibration = load_calibrations()
        xy_rms, xy_max, floor_rms, floor_max = calibration["quality"]
        print(
            f"평면 품질: XY RMS={xy_rms:.2f} mm, 최대={xy_max:.2f} mm / "
            f"바닥 RMS={floor_rms:.2f} mm, 최대={floor_max:.2f} mm"
        )
        print(
            f"저장 집기 pitch={np.degrees(calibration['pitch_rad']):.1f}도, "
            f"모델 z 오프셋={calibration['grasp_offset_m'] * 1000:.1f} mm"
        )
        print(
            f"넝쿨 회피 오프셋=+{VINE_AVOIDANCE_Z_OFFSET_M * 1000:.0f} mm "
            "(보정 JSON과 분리된 시험값)"
        )
        print("그리퍼 명령 없음 / 최종 집기 높이로 이동하지 않음")

        model_path = find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        validate_model(model)
        cap = open_camera()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)
        print("중앙 보정 카메라 자세로 이동합니다.")
        arm.move_joints(
            calibration["camera_joints"], duration=CAMERA_MOVE_DURATION_SEC
        )
        time.sleep(SETTLE_TIME_SEC)
        safe_to_park = True

        selected = choose_pumpkin(model, cap, calibration)
        cap.release()
        cap = None
        cv2.destroyAllWindows()
        if selected is None:
            raise UserCancelled

        u, v = selected
        pixel_inside, pixel_margin = inside_hull(
            (u, v), calibration["image_points"]
        )
        if not pixel_inside:
            raise ValueError(
                f"검출 중심이 보정 영상 영역 밖입니다: {pixel_margin:.1f} px"
            )

        raw_xy = pixel_to_robot_xy(u, v, calibration["homography"])
        xy = raw_xy + np.asarray(
            [TARGET_X_OFFSET_M, TARGET_Y_OFFSET_M], dtype=float
        )
        xy_inside, xy_margin = inside_hull(xy, calibration["robot_points"])
        if not xy_inside:
            raise ValueError(
                f"변환 XY가 보정 영역 밖입니다: {xy_margin * 1000:.1f} mm"
            )

        floor_z = floor_z_at(
            float(xy[0]), float(xy[1]), calibration["floor_coefficients"]
        )
        planned_grasp_z = (
            floor_z
            + calibration["grasp_offset_m"]
            + VINE_AVOIDANCE_Z_OFFSET_M
        )
        xyz_stages = [
            np.asarray(
                [xy[0], xy[1], planned_grasp_z + clearance], dtype=float
            )
            for clearance in APPROACH_CLEARANCES_M
        ]

        current_joints = np.asarray(arm.joints(), dtype=float)
        try:
            joints_stages, deltas = plan_fixed_pose_stages(
                arm,
                xyz_stages,
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 저장된 집기 각도로 안전 IK를 만들지 못했습니다: {error}")
            return

        print("\n========== YOLO 호박 접근 계획 ==========")
        print(f"검출 기준: {TARGET_PIXEL_MODE}")
        print(f"안정화 픽셀: u={u:.1f}, v={v:.1f}")
        print(
            f"원본 변환 XY [m]: x={raw_xy[0]:.4f}, y={raw_xy[1]:.4f}"
        )
        print(
            "실측 미세보정: "
            f"dx={TARGET_X_OFFSET_M * 1000:+.1f} mm, "
            f"dy={TARGET_Y_OFFSET_M * 1000:+.1f} mm"
        )
        print(f"최종 목표 XY [m]: x={xy[0]:.4f}, y={xy[1]:.4f}")
        print(f"보정 영역 경계 여유: {xy_margin * 1000:.1f} mm")
        print(f"계산 바닥 z: {floor_z:.4f} m")
        print(f"넝쿨 회피 포함 계획 집기 z: {planned_grasp_z:.4f} m")
        print(f"고정 pitch: {np.degrees(calibration['pitch_rad']):.1f}도")
        print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
        for index, (clearance, xyz, joints, delta) in enumerate(
            zip(APPROACH_CLEARANCES_M, xyz_stages, joints_stages, deltas), start=1
        ):
            delta_deg, max_delta, _total_delta = delta
            print(
                f"단계 {index}: 계획 집기점보다 {clearance * 1000:.0f} mm 위 / "
                f"XYZ={np.round(xyz, 4)}"
            )
            print(f"  관절 [deg]: {np.round(np.degrees(joints), 1)}")
            print(
                f"  이전 자세 대비 변화 [deg]: {np.round(delta_deg, 1)} "
                f"(최대 {max_delta:.1f}도)"
            )
        print("그리퍼 동작 없음 / 계획 집기점보다 30mm 아래로 내려가지 않음")
        print("=========================================")

        confirmation = input(
            "사람·케이블을 치우고 80mm 상공으로 이동하려면 MOVE_HIGH 입력: "
        ).strip()
        if confirmation != "MOVE_HIGH":
            print("MOVE_HIGH가 입력되지 않아 이동하지 않습니다.")
            return

        safe_to_park = False
        arm.move_joints(joints_stages[0], duration=HIGH_MOVE_DURATION_SEC)
        safe_to_park = True
        print("80mm 상공 도착. 그리퍼 중심과 호박 중심을 확인하세요.")

        confirmation = input(
            "정렬이 맞고 50mm 상공으로 낮추려면 MOVE_50 입력: "
        ).strip()
        if confirmation == "MOVE_50":
            safe_to_park = False
            arm.move_joints(joints_stages[1], duration=LOWER_MOVE_DURATION_SEC)
            safe_to_park = True
            print("50mm 상공 도착. 간섭과 중심을 다시 확인하세요.")

            confirmation = input(
                "정렬·높이가 안전하고 30mm 상공으로 낮추려면 MOVE_30 입력: "
            ).strip()
            if confirmation == "MOVE_30":
                safe_to_park = False
                arm.move_joints(joints_stages[2], duration=LOWER_MOVE_DURATION_SEC)
                safe_to_park = True
                print("30mm 상공 도착. 그리퍼는 닫히지 않습니다.")
                input("중심 오차를 확인한 뒤 Enter를 눌러 단계적으로 복귀: ")

                safe_to_park = False
                arm.move_joints(joints_stages[1], duration=LOWER_MOVE_DURATION_SEC)
                safe_to_park = True
            else:
                print("MOVE_30이 입력되지 않아 30mm로 내려가지 않습니다.")

            safe_to_park = False
            arm.move_joints(joints_stages[0], duration=LOWER_MOVE_DURATION_SEC)
            safe_to_park = True
        else:
            print("MOVE_50이 입력되지 않아 더 내려가지 않습니다.")

        safe_to_park = False
        arm.move_joints(
            calibration["camera_joints"], duration=RETURN_DURATION_SEC
        )
        safe_to_park = True
        print("YOLO 호박 비접촉 접근 검증이 끝났습니다.")

    except UserCancelled:
        print("목표 선택을 취소했습니다.")
    except KeyboardInterrupt:
        safe_to_park = False
        print("\n사용자가 중단했습니다. 자동 복귀를 생략합니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if safe_to_park:
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
