"""Teach and save a safe OMX camera-view pose.

The arm torque is disabled only inside ``arm.teach()``. Support the arm with
both hands while teaching. Press S in the camera window to save the pose or Q
to cancel. The arm moves to park before disconnecting.
"""

import json
from pathlib import Path

import cv2
import numpy as np

from omx_f import OmxFollower


CAMERA_INDEX = 0
OUTPUT_PATH = Path(__file__).with_name("camera_view_pose.json")


def open_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"카메라 /dev/video{CAMERA_INDEX}를 열 수 없습니다.")

    for _ in range(5):
        cap.read()
    return cap


def main():
    arm = None
    cap = None
    saved = False

    try:
        cap = open_camera()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        print("\n주의: teach 모드에서는 모터 토크가 풀립니다.")
        print("팔이 떨어지지 않도록 두 손으로 단단히 받치세요.")
        input("로봇팔을 잡은 상태에서 Enter를 누르면 teach 모드로 들어갑니다: ")

        taught_joints = None
        taught_pose = None
        window_name = "Teach Camera Pose - S: save, Q: cancel"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        with arm.teach():
            print("teach 모드입니다. 팔을 천천히 움직여 호박 영역을 비추세요.")
            print("영상 창에서 S를 누르면 저장하고, Q를 누르면 취소합니다.")

            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    raise RuntimeError("카메라 프레임을 읽지 못했습니다.")

                cv2.putText(
                    frame,
                    "Support arm - S: save / Q: cancel",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2,
                )
                cv2.imshow(window_name, frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("s"), ord("S")):
                    taught_joints = arm.joints().copy()
                    taught_pose = arm.pose().copy()
                    saved = True
                    break
                if key in (ord("q"), ord("Q")):
                    print("자세 저장을 취소했습니다.")
                    break

        # teach 블록을 빠져나오면 같은 자세에서 모터 토크가 다시 켜집니다.
        if saved:
            data = {
                "joints_rad": np.asarray(taught_joints, dtype=float).tolist(),
                "joints_deg": np.degrees(taught_joints).tolist(),
                "pose": np.asarray(taught_pose, dtype=float).tolist(),
            }
            OUTPUT_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print("\n카메라 촬영 자세를 저장했습니다.")
            print("관절각 [deg]:", np.round(np.degrees(taught_joints), 1))
            print("팔 끝 좌표:", np.round(taught_pose, 4))
            print("저장 파일:", OUTPUT_PATH)

    except KeyboardInterrupt:
        print("\n사용자가 중단했습니다.")

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
