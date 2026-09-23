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


# Innomaker arm camera.  The by-id path remains stable if /dev/video numbers
# change; /dev/video2 is the verified fallback on this machine.
CAMERA_DEVICE_PATH = Path(
    "/dev/v4l/by-id/"
    "usb-Innomaker_Innomaker-U20CAM-720P_SN0001-video-index0"
)
CAMERA_INDEX_FALLBACK = 2
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

CAMERA_POSE_PATH = Path(__file__).with_name("camera_view_pose.json")
OUTPUT_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")

CAMERA_MOVE_DURATION_SEC = 6.0
SETTLE_TIME_SEC = 1.0
MARKER_COUNT = 9

# Save only a calibration accurate enough for later approach testing.
MAX_RMS_REPROJECTION_ERROR_M = 0.008
MAX_POINT_REPROJECTION_ERROR_M = 0.015
MAX_TAUGHT_Z_RANGE_M = 0.010


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


def camera_source():
    if CAMERA_DEVICE_PATH.exists():
        return str(CAMERA_DEVICE_PATH), str(CAMERA_DEVICE_PATH)
    return CAMERA_INDEX_FALLBACK, f"/dev/video{CAMERA_INDEX_FALLBACK}"


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


def teach_floor_points(arm: OmxFollower) -> list[list[float]]:
    """Teach the gripper TCP XYZ for the 9 clicked floor markers."""
    points: list[list[float]] = []
    print("\n이제 클릭했던 기준점을 같은 번호 순서로 짚습니다.")
    print("모든 점에서 같은 그리퍼 끝부분을 책상 표면에 맞추세요.")

    for index in range(1, MARKER_COUNT + 1):
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
        points.append(xyz)
        print(
            f"기준점 {index} 저장: "
            f"x={xyz[0]:.4f}, y={xyz[1]:.4f}, z={xyz[2]:.4f} m"
        )
    return points


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


def validate_floor_and_fit(
    robot_points_xyz: list[list[float]],
    errors_m: list[float],
    rms_m: float,
    max_m: float,
) -> float:
    z_values = np.asarray(robot_points_xyz, dtype=float)[:, 2]
    z_range_m = float(np.max(z_values) - np.min(z_values))

    print("\n========== 9점 보정 품질 ==========")
    for index, error_m in enumerate(errors_m, start=1):
        print(f"{index}번 재투영 오차: {error_m * 1000:.1f} mm")
    print(f"RMS 재투영 오차: {rms_m * 1000:.1f} mm")
    print(f"최대 재투영 오차: {max_m * 1000:.1f} mm")
    print(f"9점 z 높이 범위: {z_range_m * 1000:.1f} mm")
    print("===================================")

    failures = []
    if rms_m > MAX_RMS_REPROJECTION_ERROR_M:
        failures.append(
            f"RMS {rms_m * 1000:.1f} mm > "
            f"허용 {MAX_RMS_REPROJECTION_ERROR_M * 1000:.1f} mm"
        )
    if max_m > MAX_POINT_REPROJECTION_ERROR_M:
        failures.append(
            f"최대 {max_m * 1000:.1f} mm > "
            f"허용 {MAX_POINT_REPROJECTION_ERROR_M * 1000:.1f} mm"
        )
    if z_range_m > MAX_TAUGHT_Z_RANGE_M:
        failures.append(
            f"z 범위 {z_range_m * 1000:.1f} mm > "
            f"허용 {MAX_TAUGHT_Z_RANGE_M * 1000:.1f} mm"
        )

    if failures:
        raise ValueError(
            "보정 품질 기준을 통과하지 못해 JSON을 저장하지 않습니다:\n- "
            + "\n- ".join(failures)
        )
    return z_range_m


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
    z_range_m: float,
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
            "taught_z_range_mm": float(z_range_m * 1000),
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

        cap = open_camera()
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("저장된 카메라 촬영 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=CAMERA_MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)

        frozen_frame = capture_stable_frame(cap)
        image_points = select_marker_pixels(frozen_frame)

        cap.release()
        cap = None
        cv2.destroyAllWindows()

        robot_points_xyz = teach_floor_points(arm)
        robot_points_xy = [point[:2] for point in robot_points_xyz]
        homography = calculate_homography(image_points, robot_points_xy)
        errors_m, rms_m, max_m = reprojection_statistics(
            image_points,
            robot_points_xy,
            homography,
        )
        z_range_m = validate_floor_and_fit(
            robot_points_xyz,
            errors_m,
            rms_m,
            max_m,
        )

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
            z_range_m,
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
