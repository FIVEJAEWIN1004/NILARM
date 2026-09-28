"""Calibrate one RGB camera view to the OMX ground plane.

This program does not harvest a pumpkin. It creates
``pumpkin_plane_calibration.json`` containing:

1. Four image pixels and the matching OMX-base XY positions.
2. A homography that converts a YOLO pixel position to robot XY.
3. A manually taught pumpkin grasp pose and grasp height.

The camera pose is loaded from ``camera_view_pose.json``. During every
``arm.teach()`` block the motor torque is released, so support the arm with
both hands until Enter has been pressed and the teach block has ended.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_POSE_PATH = Path(__file__).with_name("camera_view_pose.json")
OUTPUT_PATH = Path(__file__).with_name("pumpkin_plane_calibration.json")

CAMERA_MOVE_DURATION_SEC = 6.0
SETTLE_TIME_SEC = 0.8
APPROACH_CLEARANCE_M = 0.05
MARKER_COUNT = 4


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


def open_camera() -> cv2.VideoCapture:
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"카메라 /dev/video{CAMERA_INDEX}를 열 수 없습니다.")

    return cap


def capture_stable_frame(cap: cv2.VideoCapture) -> np.ndarray:
    frame = None
    for _ in range(10):
        ok, current = cap.read()
        if ok and current is not None:
            frame = current

    if frame is None:
        raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

    return frame


def select_marker_pixels(frame: np.ndarray) -> list[list[float]]:
    """Let the user click four fixed floor markers in a frozen image."""
    window_name = "Ground markers - Click 4 / S save / R reset / Q cancel"
    clicked: list[tuple[int, int]] = []

    def mouse_callback(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicked) < MARKER_COUNT:
            clicked.append((int(x), int(y)))
            print(f"화면 기준점 {len(clicked)}: pixel=({x}, {y})")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("\n정지 화면에서 바닥의 테이프 기준점 4개를 차례로 클릭하세요.")
    print("클릭한 번호와 나중에 그리퍼로 짚는 번호의 순서가 같아야 합니다.")
    print("4개 클릭 후 S: 확정, R: 다시 선택, Q: 취소")

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

        message = f"Clicked: {len(clicked)}/{MARKER_COUNT}"
        cv2.putText(
            display,
            message,
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
                print("기준점 4개를 모두 클릭한 뒤 S를 누르세요.")
                continue
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            raise CalibrationCancelled

    cv2.destroyWindow(window_name)
    return [[float(x), float(y)] for x, y in clicked]


def teach_xy_points(arm: OmxFollower) -> list[list[float]]:
    """Teach the robot XY coordinate corresponding to each clicked marker."""
    points: list[list[float]] = []

    print("\n이제 화면에서 클릭했던 기준점을 같은 번호 순서로 짚습니다.")
    for index in range(1, MARKER_COUNT + 1):
        input(
            f"\n두 손으로 팔을 받친 뒤 Enter를 누르면 기준점 {index} "
            "teach 모드로 들어갑니다: "
        )

        with arm.teach():
            print("토크가 풀렸습니다. 팔을 계속 받치세요.")
            print(f"그리퍼 끝 중심을 실제 기준점 {index}에 맞추세요.")
            input("정확히 맞춘 상태에서 Enter를 누르세요: ")
            pose = np.asarray(arm.pose(), dtype=float).copy()

        if pose.size < 3 or not np.all(np.isfinite(pose[:3])):
            raise RuntimeError(f"기준점 {index}의 로봇 좌표를 읽지 못했습니다.")

        xy = [float(pose[0]), float(pose[1])]
        points.append(xy)
        print(
            f"기준점 {index} 저장: "
            f"x={xy[0]:.4f} m, y={xy[1]:.4f} m"
        )

    return points


def read_tool_pitch(arm: OmxFollower) -> float | None:
    """Read tool pitch when supported by the installed omx_f version."""
    try:
        value = getattr(arm, "tool_pitch")
        if callable(value):
            value = value()
        result = float(value)
        return result if np.isfinite(result) else None
    except (AttributeError, TypeError, ValueError):
        return None


def teach_grasp_pose(arm: OmxFollower) -> dict[str, object]:
    print("\n마지막으로 호박 한 개의 실제 잡기 자세를 저장합니다.")
    print("그리퍼를 호박을 잡기 좋은 위치와 방향에 맞춰야 합니다.")
    input("호박을 놓고 두 손으로 팔을 받친 뒤 Enter를 누르세요: ")

    with arm.teach():
        print("토크가 풀렸습니다. 팔을 계속 받치세요.")
        print("그리퍼 끝을 호박의 잡기 위치에 맞추세요.")
        input("잡기 자세를 유지한 상태에서 Enter를 누르세요: ")
        pose = np.asarray(arm.pose(), dtype=float).copy()
        joints = np.asarray(arm.joints(), dtype=float).copy()

    if pose.size < 3 or not np.all(np.isfinite(pose[:3])):
        raise RuntimeError("잡기 자세의 손끝 좌표를 읽지 못했습니다.")
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise RuntimeError("잡기 자세의 관절각을 읽지 못했습니다.")

    pitch = read_tool_pitch(arm)
    grasp_z = float(pose[2])
    result: dict[str, object] = {
        "pose_m": pose.tolist(),
        "joints_rad": joints.tolist(),
        "joints_deg": np.degrees(joints).tolist(),
        "grasp_z_m": grasp_z,
        "approach_z_m": grasp_z + APPROACH_CLEARANCE_M,
    }
    if pitch is not None:
        result["tool_pitch_rad"] = pitch
        result["tool_pitch_deg"] = float(np.degrees(pitch))

    print("잡기 손끝 좌표 [m]:", np.round(pose[:3], 4))
    print("잡기 관절각 [deg]:", np.round(np.degrees(joints), 1))
    return result


def calculate_homography(
    image_points: list[list[float]],
    robot_points: list[list[float]],
) -> np.ndarray:
    image = np.asarray(image_points, dtype=np.float64)
    robot = np.asarray(robot_points, dtype=np.float64)

    if np.linalg.matrix_rank(np.c_[image, np.ones(MARKER_COUNT)]) < 3:
        raise ValueError("화면 기준점이 한 직선에 가깝습니다. 네 모서리로 다시 잡으세요.")
    if np.linalg.matrix_rank(np.c_[robot, np.ones(MARKER_COUNT)]) < 3:
        raise ValueError("로봇 기준점이 한 직선에 가깝습니다. 네 모서리로 다시 잡으세요.")

    homography, _ = cv2.findHomography(image, robot, method=0)
    if homography is None or not np.all(np.isfinite(homography)):
        raise RuntimeError("픽셀-로봇 좌표 변환 행렬을 계산하지 못했습니다.")

    return homography


def save_calibration(
    camera_joints: np.ndarray,
    image_points: list[list[float]],
    robot_points: list[list[float]],
    homography: np.ndarray,
    grasp: dict[str, object],
) -> None:
    data = {
        "camera": {
            "index": CAMERA_INDEX,
            "width": CAMERA_WIDTH,
            "height": CAMERA_HEIGHT,
        },
        "camera_pose": {
            "joints_rad": camera_joints.tolist(),
            "joints_deg": np.degrees(camera_joints).tolist(),
        },
        "image_points_px": image_points,
        "robot_points_xy_m": robot_points,
        "homography_px_to_robot_xy": homography.tolist(),
        "grasp": grasp,
    }

    temporary = OUTPUT_PATH.with_name(OUTPUT_PATH.name + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(OUTPUT_PATH)


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

        # The camera is no longer needed after the fixed reference image.
        cap.release()
        cap = None
        cv2.destroyAllWindows()

        robot_points = teach_xy_points(arm)
        grasp = teach_grasp_pose(arm)
        homography = calculate_homography(image_points, robot_points)

        save_calibration(
            camera_joints,
            image_points,
            robot_points,
            homography,
            grasp,
        )

        print("\n보정값과 잡기 높이를 저장했습니다.")
        print("저장 파일:", OUTPUT_PATH)
        print("이 파일을 확인하기 전에는 자동 수확 코드를 실행하지 마세요.")

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
