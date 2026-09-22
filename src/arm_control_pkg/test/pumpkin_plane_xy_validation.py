#!/usr/bin/env python3
"""Safely validate the saved 9-point pixel-to-robot XY calibration.

The user clicks one visible table marker in the same camera pose used for
calibration.  The program converts that pixel through the saved homography,
uses the saved measured floor plane, and plans 80 mm, 50 mm, and 30 mm
clearance poses with one fixed tool pitch.  Every lower stage requires a
different exact confirmation word.

It never descends to the table and never operates the gripper.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


CALIBRATION_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")

# Verified arm camera.  Never fall back to /dev/video0 (laptop camera).
CAMERA_DEVICE_PATH = Path("/dev/video2")
CAMERA_EXPECTED_NAME = "Innomaker"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

CAMERA_MOVE_DURATION_SEC = 6.0
HIGH_MOVE_DURATION_SEC = 12.0
LOWER_MOVE_DURATION_SEC = 8.0
RETURN_DURATION_SEC = 12.0
SETTLE_TIME_SEC = 1.0

# Staged validation: approach high, then descend only after separate commands.
HIGH_CLEARANCE_M = 0.080
MID_CLEARANCE_M = 0.050
LOW_CLEARANCE_M = 0.030
PITCH_CANDIDATES_DEG = (75, 80, 70, 85, 65, 60, 55, 50, 45, 40, 35)
MAX_SINGLE_JOINT_CHANGE_DEG = 65.0
MAX_TOTAL_JOINT_CHANGE_DEG = 170.0
MAX_LOWER_SINGLE_JOINT_CHANGE_DEG = 25.0
MAX_LOWER_TOTAL_JOINT_CHANGE_DEG = 65.0

# Refuse calibration files worse than the limits used when they were saved.
MAX_SAVED_RMS_ERROR_MM = 8.0
MAX_SAVED_POINT_ERROR_MM = 15.0
MAX_SAVED_FLOOR_RMS_ERROR_MM = 5.0
MAX_SAVED_FLOOR_POINT_ERROR_MM = 8.0


class UserCancelled(Exception):
    """Raised when the user cancels before target motion."""


def checked_array(value, shape, name):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} 형식이 올바르지 않습니다: {array.shape}")
    return array


def load_calibration() -> dict:
    if not CALIBRATION_PATH.is_file():
        raise FileNotFoundError(f"보정 파일이 없습니다: {CALIBRATION_PATH}")

    data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    if data.get("method") != "9_point_ground_plane_homography":
        raise ValueError("9점 평면 보정 파일이 아닙니다.")

    quality = data.get("quality", {})
    rms_mm = float(quality["rms_error_mm"])
    max_mm = float(quality["max_error_mm"])
    floor_rms_mm = float(quality["floor_plane_rms_error_mm"])
    floor_max_mm = float(quality["floor_plane_max_error_mm"])
    if rms_mm > MAX_SAVED_RMS_ERROR_MM or max_mm > MAX_SAVED_POINT_ERROR_MM:
        raise ValueError(
            f"저장된 XY 품질이 기준을 벗어납니다: RMS={rms_mm:.1f} mm, "
            f"최대={max_mm:.1f} mm"
        )
    if (
        floor_rms_mm > MAX_SAVED_FLOOR_RMS_ERROR_MM
        or floor_max_mm > MAX_SAVED_FLOOR_POINT_ERROR_MM
    ):
        raise ValueError(
            "저장된 바닥 평면 품질이 기준을 벗어납니다: "
            f"RMS={floor_rms_mm:.1f} mm, 최대={floor_max_mm:.1f} mm"
        )

    return {
        "camera_joints": checked_array(
            data["camera_pose"]["joints_rad"], (5,), "camera_pose.joints_rad"
        ),
        "image_points": checked_array(
            data["image_points_px"], (9, 2), "image_points_px"
        ),
        "robot_points_xy": checked_array(
            data["robot_points_xy_m"], (9, 2), "robot_points_xy_m"
        ),
        "homography": checked_array(
            data["homography_px_to_robot_xy"], (3, 3), "homography"
        ),
        "floor_coefficients": checked_array(
            quality["floor_plane_z_from_xy"], (3,), "floor plane"
        ),
        "quality": {
            "rms_mm": rms_mm,
            "max_mm": max_mm,
            "floor_rms_mm": floor_rms_mm,
            "floor_max_mm": floor_max_mm,
        },
    }


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
            "노트북 카메라로는 검증하지 않습니다."
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
    return cap


def capture_stable_frame(cap: cv2.VideoCapture) -> np.ndarray:
    frame = None
    for _ in range(15):
        ok, current = cap.read()
        if ok and current is not None:
            frame = current
    if frame is None:
        raise RuntimeError("팔 카메라 프레임을 읽지 못했습니다.")
    height, width = frame.shape[:2]
    if (width, height) != (CAMERA_WIDTH, CAMERA_HEIGHT):
        raise RuntimeError(
            f"영상 크기가 {width}x{height}입니다. "
            f"필요한 크기는 {CAMERA_WIDTH}x{CAMERA_HEIGHT}입니다."
        )
    return frame


def choose_test_pixel(frame: np.ndarray, image_points: np.ndarray) -> tuple[float, float]:
    window = "XY validation - click one marker / S confirm / R reset / Q cancel"
    selected: list[tuple[int, int]] = []
    boundary = cv2.convexHull(image_points.astype(np.int32).reshape(-1, 1, 2))

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            selected[:] = [(int(x), int(y))]
            print(f"선택 픽셀: ({x}, {y})")

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, on_mouse)
    print("\n우선 가운데 5번 스티커의 중심을 클릭하는 것을 권장합니다.")
    print("한 점 클릭 후 S: 확정, R: 다시 선택, Q: 취소")

    while True:
        display = frame.copy()
        cv2.polylines(display, [boundary], True, (255, 255, 0), 2)
        for index, point in enumerate(image_points, start=1):
            p = tuple(np.rint(point).astype(int))
            cv2.circle(display, p, 5, (0, 255, 255), 1)
            cv2.putText(
                display,
                str(index),
                (p[0] + 7, p[1] - 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
        if selected:
            cv2.drawMarker(
                display,
                selected[0],
                (0, 0, 255),
                cv2.MARKER_CROSS,
                24,
                2,
            )
        cv2.putText(
            display,
            "Click marker center / S confirm / R reset / Q cancel",
            (12, display.shape[0] - 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow(window, display)

        key = cv2.waitKey(20) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            raise UserCancelled
        if key in (ord("r"), ord("R")):
            selected.clear()
            print("선택을 초기화했습니다.")
        if key in (ord("s"), ord("S")):
            if not selected:
                print("먼저 스티커 중심을 클릭하세요.")
                continue
            break
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            raise UserCancelled

    cv2.destroyWindow(window)
    return float(selected[0][0]), float(selected[0][1])


def inside_hull(point, hull_points: np.ndarray) -> tuple[bool, float]:
    hull = cv2.convexHull(hull_points.astype(np.float32).reshape(-1, 1, 2))
    distance = float(
        cv2.pointPolygonTest(hull, (float(point[0]), float(point[1])), True)
    )
    return distance >= 0.0, distance


def pixel_to_robot_xy(u: float, v: float, homography: np.ndarray) -> np.ndarray:
    pixel = np.asarray([[[u, v]]], dtype=np.float32)
    xy = cv2.perspectiveTransform(pixel, homography).reshape(2).astype(float)
    if not np.all(np.isfinite(xy)):
        raise ValueError("픽셀을 유효한 로봇 XY로 변환하지 못했습니다.")
    return xy


def floor_z_at(x: float, y: float, coefficients: np.ndarray) -> float:
    a, b, c = coefficients
    z = float(a * x + b * y + c)
    if not np.isfinite(z):
        raise ValueError("바닥 평면 z 계산 결과가 올바르지 않습니다.")
    return z


def get_kinematics(arm):
    kinematics = getattr(arm, "kin", None)
    if kinematics is None:
        kinematics = getattr(arm, "_kin", None)
    if kinematics is None or not hasattr(kinematics, "inverse"):
        raise RuntimeError("OmxFollower에서 inverse kinematics를 찾지 못했습니다.")
    return kinematics


def find_staged_ik(
    arm,
    xyz_stages: list[np.ndarray],
    current_joints: np.ndarray,
):
    candidates = []
    failures = []
    kinematics = get_kinematics(arm)

    for pitch_deg in PITCH_CANDIDATES_DEG:
        try:
            stage_joints = []
            stage_deltas = []
            seed = current_joints
            for stage_index, xyz in enumerate(xyz_stages):
                target_joints = np.asarray(
                    kinematics.inverse(
                        tuple(float(value) for value in xyz),
                        seed,
                        pitch=np.radians(float(pitch_deg)),
                        roll=0.0,
                    ),
                    dtype=float,
                )
                if target_joints.shape != current_joints.shape:
                    raise ValueError("관절 배열 크기 불일치")
                if not np.all(np.isfinite(target_joints)):
                    raise ValueError("유효하지 않은 관절값")

                delta_deg = np.abs(np.degrees(target_joints - seed))
                max_delta = float(np.max(delta_deg))
                total_delta = float(np.sum(delta_deg))
                if stage_index == 0:
                    if max_delta > MAX_SINGLE_JOINT_CHANGE_DEG:
                        raise ValueError(f"80mm 접근 단일 변화 {max_delta:.1f}도")
                    if total_delta > MAX_TOTAL_JOINT_CHANGE_DEG:
                        raise ValueError(f"80mm 접근 전체 변화 {total_delta:.1f}도")
                else:
                    if max_delta > MAX_LOWER_SINGLE_JOINT_CHANGE_DEG:
                        raise ValueError(
                            f"단계 {stage_index} 하강 단일 변화 {max_delta:.1f}도"
                        )
                    if total_delta > MAX_LOWER_TOTAL_JOINT_CHANGE_DEG:
                        raise ValueError(
                            f"단계 {stage_index} 하강 전체 변화 {total_delta:.1f}도"
                        )

                stage_joints.append(target_joints)
                stage_deltas.append(
                    {
                        "delta_deg": delta_deg,
                        "max_delta_deg": max_delta,
                        "total_delta_deg": total_delta,
                    }
                )
                seed = target_joints

            candidates.append(
                {
                    "pitch_deg": float(pitch_deg),
                    "stage_joints": stage_joints,
                    "stage_deltas": stage_deltas,
                    "score": (
                        stage_deltas[0]["max_delta_deg"]
                        + 0.15 * stage_deltas[0]["total_delta_deg"]
                        + 0.20 * sum(
                            item["max_delta_deg"] for item in stage_deltas[1:]
                        )
                    ),
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


def main() -> None:
    arm = None
    cap = None
    calibration = None
    return_is_safe = False

    try:
        calibration = load_calibration()
        q = calibration["quality"]
        print(
            f"저장 보정 품질: XY RMS={q['rms_mm']:.2f} mm, "
            f"최대={q['max_mm']:.2f} mm / "
            f"바닥 RMS={q['floor_rms_mm']:.2f} mm, "
            f"최대={q['floor_max_mm']:.2f} mm"
        )
        print("이 프로그램은 그리퍼를 작동하거나 책상으로 하강하지 않습니다.")

        cap = open_camera()
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("보정에 사용한 카메라 자세로 이동합니다.")
        arm.move_joints(
            calibration["camera_joints"], duration=CAMERA_MOVE_DURATION_SEC
        )
        time.sleep(SETTLE_TIME_SEC)
        return_is_safe = True

        frame = capture_stable_frame(cap)
        u, v = choose_test_pixel(frame, calibration["image_points"])

        pixel_inside, pixel_margin = inside_hull(
            (u, v), calibration["image_points"]
        )
        if not pixel_inside:
            print(
                f"[이동 금지] 선택점이 보정 화면 영역 밖입니다: "
                f"경계 거리 {pixel_margin:.1f} px"
            )
            return

        xy = pixel_to_robot_xy(u, v, calibration["homography"])
        xy_inside, xy_margin = inside_hull(xy, calibration["robot_points_xy"])
        if not xy_inside:
            print(
                f"[이동 금지] 변환된 XY가 로봇 보정 영역 밖입니다: "
                f"경계 거리 {xy_margin * 1000:.1f} mm"
            )
            return

        floor_z = floor_z_at(
            float(xy[0]), float(xy[1]), calibration["floor_coefficients"]
        )
        clearance_stages_m = (
            HIGH_CLEARANCE_M,
            MID_CLEARANCE_M,
            LOW_CLEARANCE_M,
        )
        xyz_stages = [
            np.asarray([xy[0], xy[1], floor_z + clearance], dtype=float)
            for clearance in clearance_stages_m
        ]

        cap.release()
        cap = None
        cv2.destroyAllWindows()

        current_joints = np.asarray(arm.joints(), dtype=float)
        solution = find_staged_ik(arm, xyz_stages, current_joints)
        if solution is None:
            print("[이동 금지] 세 높이를 모두 만족하는 안전 IK가 없습니다.")
            return

        print("\n========== 단계별 비접촉 검증 계획 ==========")
        print(f"선택 픽셀: u={u:.1f}, v={v:.1f}")
        print(f"변환 XY [m]: x={xy[0]:.4f}, y={xy[1]:.4f}")
        print(f"계산 바닥 z: {floor_z:.4f} m")
        print(f"보정 영역 경계 여유: {xy_margin * 1000:.1f} mm")
        print(f"선택 pitch: {solution['pitch_deg']:.1f}도")
        print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
        for index, (clearance, xyz, joints, delta) in enumerate(
            zip(
                clearance_stages_m,
                xyz_stages,
                solution["stage_joints"],
                solution["stage_deltas"],
            ),
            start=1,
        ):
            print(
                f"단계 {index}: 바닥보다 {clearance * 1000:.0f} mm 위 / "
                f"목표 z={xyz[2]:.4f} m"
            )
            print(f"  관절 [deg]: {np.round(np.degrees(joints), 1)}")
            print(f"  이전 자세 대비 변화 [deg]: {np.round(delta['delta_deg'], 1)}")
            print(f"  최대 변화: {delta['max_delta_deg']:.1f}도")
        print("그리퍼 동작 없음 / 30 mm보다 낮게 내려가지 않음")
        print("============================================")

        confirmation = input(
            "사람·케이블을 치우고 80mm 상공으로 이동하려면 MOVE_HIGH 입력: "
        ).strip()
        if confirmation != "MOVE_HIGH":
            print("MOVE_HIGH가 입력되지 않아 이동하지 않습니다.")
            return

        print(f"{HIGH_MOVE_DURATION_SEC:.1f}초 동안 80mm 상공으로 이동합니다.")
        return_is_safe = False
        arm.move_joints(
            solution["stage_joints"][0], duration=HIGH_MOVE_DURATION_SEC
        )
        return_is_safe = True
        print("80mm 상공 도착. XY 정렬과 주변 간섭을 확인하세요.")

        confirmation = input(
            "정렬이 맞고 50mm 상공으로 낮추려면 MOVE_50 입력: "
        ).strip()
        if confirmation != "MOVE_50":
            print("MOVE_50이 입력되지 않아 하강하지 않고 복귀합니다.")
        else:
            return_is_safe = False
            arm.move_joints(
                solution["stage_joints"][1], duration=LOWER_MOVE_DURATION_SEC
            )
            return_is_safe = True
            print("50mm 상공 도착. 그리퍼와 책상 사이 여유를 직접 확인하세요.")

            confirmation = input(
                "정렬·높이가 안전하고 30mm 상공으로 낮추려면 MOVE_30 입력: "
            ).strip()
            if confirmation != "MOVE_30":
                print("MOVE_30이 입력되지 않아 30mm로 하강하지 않습니다.")
            else:
                return_is_safe = False
                arm.move_joints(
                    solution["stage_joints"][2], duration=LOWER_MOVE_DURATION_SEC
                )
                return_is_safe = True
                print("30mm 상공 도착. 접촉하지 말고 XY와 실제 높이를 확인하세요.")
                input("확인이 끝나면 Enter를 눌러 단계적으로 복귀: ")

                return_is_safe = False
                arm.move_joints(
                    solution["stage_joints"][1], duration=LOWER_MOVE_DURATION_SEC
                )
                return_is_safe = True

            # Whether or not 30 mm was entered, retreat from 50 mm to 80 mm.
            return_is_safe = False
            arm.move_joints(
                solution["stage_joints"][0], duration=LOWER_MOVE_DURATION_SEC
            )
            return_is_safe = True

        return_is_safe = False
        arm.move_joints(
            calibration["camera_joints"], duration=RETURN_DURATION_SEC
        )
        return_is_safe = True
        print("단계별 비접촉 높이 검증이 끝났습니다.")

    except UserCancelled:
        print("검증을 취소했습니다.")
    except KeyboardInterrupt:
        return_is_safe = False
        print("\n사용자가 중단했습니다. 자동 복귀를 생략합니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if return_is_safe and calibration is not None:
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
