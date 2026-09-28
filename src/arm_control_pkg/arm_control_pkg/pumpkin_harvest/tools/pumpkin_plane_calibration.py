"""Create a 9-point pixel-to-OMX ground-plane calibration.

This stage calibrates only the camera ground plane.  It never detects or
harvests pumpkins and it does not teach a grasp pose.  Nine floor markers are
clicked in one frozen image and then touched with the gripper TCP in the same
order.  A homography is saved only when its reprojection error and the taught
floor-height consistency pass conservative checks.
"""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


# Verified from v4l2-ctl on this machine:
#   /dev/video2 = Innomaker-U20CAM-720P (arm camera, index0)
# Never fall back to index 0 because that is the laptop HD Camera.
CAMERA_DEVICE_PATH = Path("/dev/video2")
CAMERA_EXPECTED_NAME = "Innomaker"
CAMERA_INDEX_FALLBACK = 2
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

CAMERA_POSE_PATH = Path(__file__).resolve().parent.parent.joinpath("camera_view_pose.json")
OUTPUT_PATH = Path(__file__).resolve().parent.parent.joinpath("pumpkin_plane_calibration.json")

CAMERA_MOVE_DURATION_SEC = 6.0
SETTLE_TIME_SEC = 1.0
MARKER_COUNT = 9

# Recovery data copied from the failed 2026-09-20 run.  It is offered only
# when the physical markers have not moved.  The user explicitly chooses
# RESUME or NEW at startup, so stale points are never used silently.
RECOVERY_IMAGE_POINTS = [
    [24.0, 22.0],
    [297.0, 25.0],
    [612.0, 25.0],
    [30.0, 211.0],
    [336.0, 233.0],
    [629.0, 260.0],
    [50.0, 414.0],
    [358.0, 460.0],
    [615.0, 448.0],
]
RECOVERY_ROBOT_POINTS_XYZ = [
    [0.2337, 0.0873, -0.0155],
    [0.2101, -0.0131, -0.0219],
    [0.2420, -0.1342, -0.0176],
    [0.1524, 0.0772, -0.0105],
    [0.1521, -0.0258, -0.0105],
    [0.1490, -0.1434, -0.0084],
    [0.0801, 0.0664, -0.0105],
    [0.0804, -0.0460, 0.0030],
    [0.0779, -0.1513, 0.0011],
]

# Save only a calibration accurate enough for later approach testing.
MAX_RMS_REPROJECTION_ERROR_M = 0.008
MAX_POINT_REPROJECTION_ERROR_M = 0.015
# The raw robot z values can change systematically across the table because
# the taught TCP and the real gripper contact point are not identical.  Judge
# contact consistency by deviation from the best-fit floor plane instead.
MAX_FLOOR_PLANE_RMS_DEVIATION_M = 0.005
MAX_FLOOR_PLANE_POINT_DEVIATION_M = 0.008


class CalibrationCancelled(Exception):
    """Raised when the user safely cancels calibration."""


def load_camera_joints() -> np.ndarray:
    if not CAMERA_POSE_PATH.is_file():
        raise FileNotFoundError(
            f"카메라 자세 파일이 없습니다: {CAMERA_POSE_PATH}\n"
            "먼저 camera_pose_teach.py로 촬영 자세를 저장하세요."
        )

    data = json.loads(CAMERA_POSE_PATH.read_text(encoding="utf-8"))
    joints = np.asarray(data.get("joints_rad"), dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError("camera_view_pose.json의 joints_rad가 올바르지 않습니다.")
    return joints


def camera_source() -> tuple[str, str]:
    if not CAMERA_DEVICE_PATH.exists():
        raise RuntimeError(
            f"팔 카메라 장치가 없습니다: {CAMERA_DEVICE_PATH}\n"
            "USB 연결과 v4l2-ctl --list-devices 결과를 확인하세요."
        )

    sysfs_name_path = Path(
        f"/sys/class/video4linux/{CAMERA_DEVICE_PATH.name}/name"
    )
    if not sysfs_name_path.is_file():
        raise RuntimeError(
            f"카메라 이름을 확인할 수 없습니다: {sysfs_name_path}"
        )

    device_name = sysfs_name_path.read_text(encoding="utf-8").strip()
    if CAMERA_EXPECTED_NAME.lower() not in device_name.lower():
        raise RuntimeError(
            f"실행 중단: {CAMERA_DEVICE_PATH}는 팔 카메라가 아닙니다.\n"
            f"감지된 이름: {device_name}\n"
            f"필요한 이름: {CAMERA_EXPECTED_NAME}\n"
            "노트북 카메라로는 보정하지 않습니다."
        )

    return str(CAMERA_DEVICE_PATH), f"{CAMERA_DEVICE_PATH} ({device_name})"


def open_camera() -> cv2.VideoCapture:
    source, label = camera_source()
    print(f"카메라 입력: {label} (Innomaker 로봇팔 카메라)")
    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"카메라 {label}를 열 수 없습니다.")
    return cap


def capture_stable_frame(cap: cv2.VideoCapture) -> np.ndarray:
    frame = None
    for _ in range(15):
        ok, current = cap.read()
        if ok and current is not None:
            frame = current
    if frame is None:
        raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

    height, width = frame.shape[:2]
    if (width, height) != (CAMERA_WIDTH, CAMERA_HEIGHT):
        raise RuntimeError(
            f"실제 영상 크기 {width}x{height}가 "
            f"설정 {CAMERA_WIDTH}x{CAMERA_HEIGHT}와 다릅니다."
        )
    return frame


def select_marker_pixels(frame: np.ndarray) -> list[list[float]]:
    """Click 9 floor markers in row-major order in a frozen image."""
    window_name = "Ground 9 points - Click / S save / R reset / Q cancel"
    clicked: list[tuple[int, int]] = []

    def mouse_callback(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicked) < MARKER_COUNT:
            clicked.append((int(x), int(y)))
            print(f"화면 기준점 {len(clicked)}: pixel=({x}, {y})")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("\n책상 평면의 기준점 9개를 아래 순서로 클릭하세요.")
    print("1 2 3  : 화면의 먼 쪽, 왼쪽에서 오른쪽")
    print("4 5 6  : 화면의 중간, 왼쪽에서 오른쪽")
    print("7 8 9  : 화면의 가까운 쪽, 왼쪽에서 오른쪽")
    print("나중에 그리퍼로 짚는 순서도 반드시 1→9로 같아야 합니다.")
    print("9개 클릭 후 S: 확정, R: 다시 선택, Q: 취소")

    while True:
        display = frame.copy()
        for index, (x, y) in enumerate(clicked, start=1):
            cv2.circle(display, (x, y), 7, (0, 0, 255), -1)
            cv2.putText(
                display,
                str(index),
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

        cv2.putText(
            display,
            f"Clicked: {len(clicked)}/{MARKER_COUNT}",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            display,
            "S: save   R: reset   Q: cancel",
            (15, display.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
        )
        cv2.imshow(window_name, display)

        key = cv2.waitKey(20) & 0xFF
        if key in (ord("r"), ord("R")):
            clicked.clear()
            print("화면 기준점을 초기화했습니다.")
        elif key in (ord("q"), ord("Q")):
            raise CalibrationCancelled
        elif key in (ord("s"), ord("S")):
            if len(clicked) != MARKER_COUNT:
                print("기준점 9개를 모두 클릭한 뒤 S를 누르세요.")
                continue
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            raise CalibrationCancelled

    cv2.destroyWindow(window_name)
    return [[float(x), float(y)] for x, y in clicked]


def teach_floor_point(arm: OmxFollower, index: int) -> list[float]:
    """Teach one marker so a failed point can be measured again."""
    input(
        f"\n팔을 두 손으로 받친 뒤 Enter를 누르면 기준점 {index}의 "
        "teach 모드로 들어갑니다: "
    )
    with arm.teach():
        print("토크가 풀렸습니다. 팔을 계속 받치세요.")
        print(f"그리퍼 끝 중심을 실제 기준점 {index}에 맞추세요.")
        input("정확히 맞춘 상태에서 Enter를 누르세요: ")
        pose = np.asarray(arm.pose(), dtype=float).copy()

    if pose.size < 3 or not np.all(np.isfinite(pose[:3])):
        raise RuntimeError(f"기준점 {index}의 로봇 좌표를 읽지 못했습니다.")

    xyz = [float(pose[0]), float(pose[1]), float(pose[2])]
    print(
        f"기준점 {index} 저장: "
        f"x={xyz[0]:.4f}, y={xyz[1]:.4f}, z={xyz[2]:.4f} m"
    )
    return xyz


def teach_floor_points(arm: OmxFollower) -> list[list[float]]:
    """Teach the gripper TCP XYZ for the 9 clicked floor markers."""
    print("\n이제 클릭했던 기준점을 같은 번호 순서로 짚습니다.")
    print("모든 점에서 같은 그리퍼 끝부분을 책상 표면에 맞추세요.")
    return [teach_floor_point(arm, index) for index in range(1, MARKER_COUNT + 1)]


def calculate_homography(
    image_points: list[list[float]],
    robot_points_xy: list[list[float]],
) -> np.ndarray:
    image = np.asarray(image_points, dtype=np.float64)
    robot = np.asarray(robot_points_xy, dtype=np.float64)

    if np.linalg.matrix_rank(np.c_[image, np.ones(MARKER_COUNT)]) < 3:
        raise ValueError("화면 기준점이 한 직선에 가깝습니다. 3x3 형태로 다시 잡으세요.")
    if np.linalg.matrix_rank(np.c_[robot, np.ones(MARKER_COUNT)]) < 3:
        raise ValueError("로봇 기준점이 한 직선에 가깝습니다. 3x3 형태로 다시 잡으세요.")

    homography, _ = cv2.findHomography(image, robot, method=0)
    if homography is None or not np.all(np.isfinite(homography)):
        raise RuntimeError("픽셀-로봇 좌표 변환 행렬을 계산하지 못했습니다.")
    return homography


def reprojection_statistics(
    image_points: list[list[float]],
    robot_points_xy: list[list[float]],
    homography: np.ndarray,
) -> tuple[list[float], float, float]:
    image = np.asarray(image_points, dtype=np.float32).reshape(-1, 1, 2)
    actual = np.asarray(robot_points_xy, dtype=float)
    predicted = cv2.perspectiveTransform(
        image,
        np.asarray(homography, dtype=np.float64),
    ).reshape(-1, 2)
    errors_m = np.linalg.norm(predicted - actual, axis=1)
    rms_m = float(np.sqrt(np.mean(np.square(errors_m))))
    max_m = float(np.max(errors_m))
    return errors_m.tolist(), rms_m, max_m


def evaluate_floor_and_fit(
    robot_points_xyz: list[list[float]],
    errors_m: list[float],
    rms_m: float,
    max_m: float,
) -> dict:
    points = np.asarray(robot_points_xyz, dtype=float)
    z_values = points[:, 2]
    z_range_m = float(np.max(z_values) - np.min(z_values))

    # z = ax + by + c represents the floor as measured by the robot model.
    floor_matrix = np.c_[points[:, 0], points[:, 1], np.ones(MARKER_COUNT)]
    floor_coefficients, *_ = np.linalg.lstsq(
        floor_matrix, z_values, rcond=None
    )
    fitted_z = floor_matrix @ floor_coefficients
    floor_residuals_m = z_values - fitted_z
    floor_rms_m = float(np.sqrt(np.mean(np.square(floor_residuals_m))))
    floor_max_m = float(np.max(np.abs(floor_residuals_m)))

    print("\n========== 9점 보정 품질 ==========")
    for index, (error_m, floor_residual_m) in enumerate(
        zip(errors_m, floor_residuals_m), start=1
    ):
        print(
            f"{index}번: XY 오차 {error_m * 1000:.1f} mm / "
            f"바닥 평면 높이 오차 {floor_residual_m * 1000:+.1f} mm"
        )
    print(f"RMS 재투영 오차: {rms_m * 1000:.1f} mm")
    print(f"최대 재투영 오차: {max_m * 1000:.1f} mm")
    print(f"원시 z 높이 범위(참고): {z_range_m * 1000:.1f} mm")
    print(f"바닥 평면 기준 RMS 높이 오차: {floor_rms_m * 1000:.1f} mm")
    print(f"바닥 평면 기준 최대 높이 오차: {floor_max_m * 1000:.1f} mm")
    print("===================================")

    failures: list[str] = []
    retry_indices: set[int] = set()

    xy_bad = [
        index
        for index, error_m in enumerate(errors_m, start=1)
        if error_m > MAX_POINT_REPROJECTION_ERROR_M
    ]
    retry_indices.update(xy_bad)

    if rms_m > MAX_RMS_REPROJECTION_ERROR_M:
        failures.append(
            f"RMS {rms_m * 1000:.1f} mm > "
            f"허용 {MAX_RMS_REPROJECTION_ERROR_M * 1000:.1f} mm"
        )
        if not xy_bad:
            retry_indices.add(int(np.argmax(errors_m)) + 1)
    if max_m > MAX_POINT_REPROJECTION_ERROR_M:
        failures.append(
            f"최대 {max_m * 1000:.1f} mm > "
            f"허용 {MAX_POINT_REPROJECTION_ERROR_M * 1000:.1f} mm"
        )

    height_bad = [
        index
        for index, residual_m in enumerate(floor_residuals_m, start=1)
        if abs(residual_m) > MAX_FLOOR_PLANE_POINT_DEVIATION_M
    ]
    retry_indices.update(height_bad)

    if floor_rms_m > MAX_FLOOR_PLANE_RMS_DEVIATION_M:
        failures.append(
            f"바닥 평면 RMS 높이 오차 {floor_rms_m * 1000:.1f} mm > "
            f"허용 {MAX_FLOOR_PLANE_RMS_DEVIATION_M * 1000:.1f} mm"
        )
        if not height_bad:
            retry_indices.add(int(np.argmax(np.abs(floor_residuals_m))) + 1)
    if floor_max_m > MAX_FLOOR_PLANE_POINT_DEVIATION_M:
        failures.append(
            f"바닥 평면 최대 높이 오차 {floor_max_m * 1000:.1f} mm > "
            f"허용 {MAX_FLOOR_PLANE_POINT_DEVIATION_M * 1000:.1f} mm"
        )

    if failures:
        print("보정 품질 기준을 통과하지 못했습니다:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "재측정 추천 번호: "
            + ", ".join(str(index) for index in sorted(retry_indices))
        )

    return {
        "passed": not failures,
        "failures": failures,
        "retry_indices": sorted(retry_indices),
        "z_range_m": z_range_m,
        "floor_coefficients": floor_coefficients.tolist(),
        "floor_residuals_m": floor_residuals_m.tolist(),
        "floor_rms_m": floor_rms_m,
        "floor_max_m": floor_max_m,
    }


def ask_retry_indices(suggested: list[int]) -> list[int]:
    suggestion = ",".join(str(index) for index in suggested)
    while True:
        answer = input(
            f"재측정할 번호를 입력하세요 (예: {suggestion or '2'} 또는 2,8 / "
            "Q: 저장 없이 종료): "
        ).strip()
        if answer.upper() == "Q":
            raise CalibrationCancelled

        tokens = answer.replace(",", " ").split()
        try:
            indices = sorted(set(int(token) for token in tokens))
        except ValueError:
            print("번호만 입력하세요. 예: 2 또는 2,8")
            continue

        if not indices or any(index < 1 or index > MARKER_COUNT for index in indices):
            print(f"1부터 {MARKER_COUNT}까지의 번호를 입력하세요.")
            continue
        return indices


def ask_resume_previous_run() -> bool:
    print("\n방금 실패한 9점 측정값을 이 파일에 복구해 두었습니다.")
    print("카메라, 로봇 베이스, 책상 스티커 9개를 움직이지 않았을 때만 RESUME하세요.")
    while True:
        answer = input(
            "기존 9점에서 이어하려면 RESUME / 처음부터 하려면 NEW / 종료 Q: "
        ).strip().upper()
        if answer == "RESUME":
            return True
        if answer == "NEW":
            return False
        if answer == "Q":
            raise CalibrationCancelled
        print("RESUME, NEW 또는 Q 중 하나를 입력하세요.")


def backup_existing_output() -> Path | None:
    if not OUTPUT_PATH.is_file():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = OUTPUT_PATH.with_name(
        f"{OUTPUT_PATH.stem}_backup_{stamp}{OUTPUT_PATH.suffix}"
    )
    shutil.copy2(OUTPUT_PATH, backup)
    return backup


def save_calibration(
    camera_joints: np.ndarray,
    image_points: list[list[float]],
    robot_points_xyz: list[list[float]],
    homography: np.ndarray,
    errors_m: list[float],
    rms_m: float,
    max_m: float,
    floor_quality: dict,
) -> None:
    robot_points_xy = [point[:2] for point in robot_points_xyz]
    data = {
        "schema_version": 2,
        "method": "9_point_ground_plane_homography",
        "camera": {
            "index": CAMERA_INDEX_FALLBACK,
            "device_path": str(CAMERA_DEVICE_PATH),
            "width": CAMERA_WIDTH,
            "height": CAMERA_HEIGHT,
        },
        "camera_pose": {
            "joints_rad": camera_joints.tolist(),
            "joints_deg": np.degrees(camera_joints).tolist(),
        },
        "image_points_px": image_points,
        "robot_points_xy_m": robot_points_xy,
        "robot_points_xyz_m": robot_points_xyz,
        "homography_px_to_robot_xy": homography.tolist(),
        "quality": {
            "point_errors_mm": [float(value * 1000) for value in errors_m],
            "rms_error_mm": float(rms_m * 1000),
            "max_error_mm": float(max_m * 1000),
            "taught_z_range_mm": float(floor_quality["z_range_m"] * 1000),
            "floor_plane_z_from_xy": floor_quality["floor_coefficients"],
            "floor_plane_point_residuals_mm": [
                float(value * 1000)
                for value in floor_quality["floor_residuals_m"]
            ],
            "floor_plane_rms_error_mm": float(
                floor_quality["floor_rms_m"] * 1000
            ),
            "floor_plane_max_error_mm": float(
                floor_quality["floor_max_m"] * 1000
            ),
        },
        # Grasp calibration is intentionally a later, separate stage.
        "grasp": None,
    }

    backup = backup_existing_output()
    temporary = OUTPUT_PATH.with_name(OUTPUT_PATH.name + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(OUTPUT_PATH)
    if backup is not None:
        print(f"기존 JSON 백업: {backup}")


def main() -> None:
    arm = None
    cap = None

    try:
        camera_joints = load_camera_joints()
        print("저장된 촬영 관절각 [deg]:", np.round(np.degrees(camera_joints), 1))
        resume_previous = ask_resume_previous_run()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        if resume_previous:
            image_points = [point.copy() for point in RECOVERY_IMAGE_POINTS]
            robot_points_xyz = [
                point.copy() for point in RECOVERY_ROBOT_POINTS_XYZ
            ]
            print("이전 화면 좌표와 로봇 좌표 9개를 불러왔습니다.")
            print("먼저 품질을 계산한 뒤 재측정 추천 번호를 표시합니다.")
        else:
            cap = open_camera()
            print("저장된 카메라 촬영 자세로 이동합니다.")
            arm.move_joints(camera_joints, duration=CAMERA_MOVE_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            frozen_frame = capture_stable_frame(cap)
            image_points = select_marker_pixels(frozen_frame)

            cap.release()
            cap = None
            cv2.destroyAllWindows()

            robot_points_xyz = teach_floor_points(arm)

        while True:
            robot_points_xy = [point[:2] for point in robot_points_xyz]
            homography = calculate_homography(image_points, robot_points_xy)
            errors_m, rms_m, max_m = reprojection_statistics(
                image_points,
                robot_points_xy,
                homography,
            )
            floor_quality = evaluate_floor_and_fit(
                robot_points_xyz,
                errors_m,
                rms_m,
                max_m,
            )
            if floor_quality["passed"]:
                break

            retry_indices = ask_retry_indices(floor_quality["retry_indices"])
            print(
                "\n선택한 기준점만 다시 측정합니다: "
                + ", ".join(str(index) for index in retry_indices)
            )
            for index in retry_indices:
                robot_points_xyz[index - 1] = teach_floor_point(arm, index)
            print("선택한 점의 재측정이 끝났습니다. 품질을 다시 계산합니다.")

        print("\n품질 기준을 통과했습니다.")
        confirmation = input(
            "기존 JSON을 백업하고 새 평면 보정을 저장하려면 SAVE 입력: "
        ).strip()
        if confirmation != "SAVE":
            print("SAVE가 입력되지 않아 JSON을 저장하지 않습니다.")
            return

        save_calibration(
            camera_joints,
            image_points,
            robot_points_xyz,
            homography,
            errors_m,
            rms_m,
            max_m,
            floor_quality,
        )
        print("새 평면 보정을 저장했습니다:", OUTPUT_PATH)
        print("집기 자세는 아직 저장하지 않았습니다.")

    except CalibrationCancelled:
        print("\n보정을 취소했습니다. 파일을 저장하지 않았습니다.")
    except KeyboardInterrupt:
        print("\n사용자가 보정을 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
