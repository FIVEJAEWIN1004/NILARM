"""Scan, count, and repeatedly harvest pumpkins into a taught front bin.

The scan functions are reused from pumpkin_scan_count.py. After a complete
scan, valid pumpkins are harvested nearest-first. Actual motion starts only
when the operator types HARVEST ALL. Each pumpkin is lifted, carried to the
taught front-bin pose, released, and followed by the next target.
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
    CALIBRATION_PATH,
    FIRST_MOVE_DURATION_SEC,
    JOINT1_SAFE_LIMIT_DEG,
    MODEL_PATH,
    MOVE_DURATION_SEC,
    SCAN_OFFSETS_DEG,
    SETTLE_TIME_SEC,
    load_calibration,
    movement_duration,
    observe_view,
    open_camera,
    print_summary,
    valid_clusters,
    validate_model,
)


APPROACH_DURATION_SEC = 6.0
DESCEND_DURATION_SEC = 4.0
LIFT_DURATION_SEC = 4.0
GRIPPER_WAIT_SEC = 1.5
BIN_MOVE_DURATION_SEC = 8.0
RETURN_TO_CENTER_DURATION_SEC = 10.0
BIN_POSE_PATH = Path(__file__).with_name("pumpkin_bin_pose.json")


def load_grasp_settings():
    """Load the grasp height and pitch taught during plane calibration."""
    data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    grasp = data.get("grasp")
    if not isinstance(grasp, dict):
        raise ValueError(
            "보정 파일에 grasp 정보가 없습니다. "
            "pumpkin_plane_calibration.py를 다시 실행하세요."
        )

    settings = {
        "grasp_z": float(grasp["grasp_z_m"]),
        "approach_z": float(grasp["approach_z_m"]),
        "pitch": float(grasp["tool_pitch_rad"]),
    }
    if not all(math.isfinite(value) for value in settings.values()):
        raise ValueError("보정 파일의 grasp 값에 유효하지 않은 수가 있습니다.")
    if settings["approach_z"] <= settings["grasp_z"]:
        raise ValueError("approach_z_m은 grasp_z_m보다 높아야 합니다.")
    return settings


def load_bin_joints():
    if not BIN_POSE_PATH.is_file():
        raise FileNotFoundError(
            f"적재함 자세 파일이 없습니다: {BIN_POSE_PATH}\n"
            "먼저 pumpkin_bin_pose_teach.py를 실행하세요."
        )

    data = json.loads(BIN_POSE_PATH.read_text(encoding="utf-8"))
    joints = np.asarray(data["bin_joints_rad"], dtype=float)
    if joints.shape != (5,) or not np.all(np.isfinite(joints)):
        raise ValueError("pumpkin_bin_pose.json의 관절값이 올바르지 않습니다.")

    joint1_deg = float(np.degrees(joints[0]))
    if abs(joint1_deg) > 30.0:
        raise ValueError(
            f"적재함 joint1={joint1_deg:.1f}도가 정면 범위(-30~+30도)가 아닙니다."
        )
    return joints


def ordered_targets(clusters):
    """Harvest nearer pumpkins first to reduce long loaded-arm travel."""
    return sorted(
        valid_clusters(clusters),
        key=lambda item: math.hypot(item.x, item.y),
    )


def grasp_one_pumpkin(arm, target, grasp, motion_state):
    x = float(target.x)
    y = float(target.y)
    approach_z = grasp["approach_z"]
    grasp_z = grasp["grasp_z"]
    pitch = grasp["pitch"]

    print("\n[수확] 그리퍼를 엽니다.")
    arm.open_gripper()
    time.sleep(GRIPPER_WAIT_SEC)

    print(
        f"[수확] 호박 위로 이동: "
        f"x={x:.3f}, y={y:.3f}, z={approach_z:.3f} m"
    )
    arm.move_to(
        x,
        y,
        approach_z,
        duration=APPROACH_DURATION_SEC,
        pitch=pitch,
    )

    print(f"[수확] 실제 잡기 높이 z={grasp_z:.3f} m까지 하강합니다.")
    arm.move_linear(
        x,
        y,
        grasp_z,
        duration=DESCEND_DURATION_SEC,
        pitch=pitch,
    )

    print("[수확] 그리퍼를 닫아 호박을 잡습니다.")
    arm.close_gripper()
    motion_state["holding"] = True
    time.sleep(GRIPPER_WAIT_SEC)

    # Lift well clear of the floor before moving toward the front bin.
    transport_z = approach_z + 0.08
    print(f"[수확] 회전 전 안전 높이 z={transport_z:.3f} m까지 들어 올립니다.")
    arm.move_linear(
        x,
        y,
        transport_z,
        duration=LIFT_DURATION_SEC,
        pitch=pitch,
    )


def deposit_in_bin(arm, bin_joints, camera_joints, motion_state):
    """Move to the taught front-bin pose, release, and return to camera pose."""
    print("[적재] 저장된 정면 적재함 자세로 이동합니다.")
    arm.move_joints(bin_joints, duration=BIN_MOVE_DURATION_SEC)
    time.sleep(0.5)

    print("[적재] 그리퍼를 열어 호박을 적재합니다.")
    arm.open_gripper()
    motion_state["holding"] = False
    time.sleep(GRIPPER_WAIT_SEC)

    print("[적재] 다음 수확을 위해 카메라 기준 자세로 돌아갑니다.")
    arm.move_joints(camera_joints, duration=BIN_MOVE_DURATION_SEC)
    time.sleep(SETTLE_TIME_SEC)


def main():
    arm = None
    cap = None
    calibration = None
    motion_state = {"holding": False}

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        calibration = load_calibration()
        grasp = load_grasp_settings()
        bin_joints = load_bin_joints()
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        print("YOLO 클래스:", model.names)

        cap = open_camera(calibration)
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        print("저장된 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)

        global_clusters = []
        view_results = []
        display_state = {"show_total": False}
        current_offset_deg = 0.0
        stop_requested = False

        for view_index, offset_deg in enumerate(SCAN_OFFSETS_DEG):
            target_joint1_deg = base_joint1_deg + offset_deg
            if abs(target_joint1_deg) > JOINT1_SAFE_LIMIT_DEG:
                print(
                    f"[건너뜀] offset={offset_deg:+.0f}도, "
                    f"joint1={target_joint1_deg:.1f}도: 안전 범위 밖"
                )
                continue

            target_joints = camera_joints.copy()
            target_joints[0] = np.radians(target_joint1_deg)
            move_duration = (
                FIRST_MOVE_DURATION_SEC
                if view_index == 0
                else movement_duration(offset_deg - current_offset_deg)
            )
            print(
                f"[이동] 기준 {offset_deg:+.0f}도 "
                f"(joint1={target_joint1_deg:.1f}도, {move_duration:.1f}초)"
            )
            arm.move_joints(target_joints, duration=move_duration)
            current_offset_deg = offset_deg
            time.sleep(SETTLE_TIME_SEC)

            count, stop_requested = observe_view(
                model,
                cap,
                calibration,
                offset_deg,
                view_index,
                global_clusters,
                display_state,
            )
            view_results.append((offset_deg, count))
            print(f"[인식] 기준 {offset_deg:+.0f}도: 화면 내 {count}개")
            if stop_requested:
                break

        print_summary(view_results, global_clusters)

        cap.release()
        cap = None
        cv2.destroyAllWindows()

        if stop_requested:
            print("사용자가 스캔을 중단했으므로 수확하지 않습니다.")
            return

        print("첫 수확 전에 중앙 카메라 자세로 돌아갑니다.")
        arm.move_joints(
            camera_joints,
            duration=RETURN_TO_CENTER_DURATION_SEC,
        )
        time.sleep(SETTLE_TIME_SEC)

        targets = ordered_targets(global_clusters)
        if not targets:
            print("유효한 호박이 없어 수확하지 않습니다.")
            return

        print("\n========== 실제 수확 목표 ==========")
        for index, target in enumerate(targets, start=1):
            print(
                f"{index:02d}. x={target.x:.3f} m, y={target.y:.3f} m, "
                f"confidence={target.confidence:.2f}"
            )
        print(f"접근 z={grasp['approach_z']:.3f} m")
        print(f"실제 잡기 z={grasp['grasp_z']:.3f} m")
        print(
            "적재함 joint1="
            f"{float(np.degrees(bin_joints[0])):.1f}도"
        )
        print("====================================")
        print("주변 사람, 케이블, 노트북과 충돌 위험이 없는지 확인하세요.")

        confirmation = input(
            f"호박 {len(targets)}개를 차례로 수확·적재하려면 "
            "HARVEST ALL 입력: "
        ).strip()
        if confirmation != "HARVEST ALL":
            print("수확을 취소했습니다.")
            return

        harvested_count = 0
        for index, target in enumerate(targets, start=1):
            print(f"\n========== {index}/{len(targets)}번 호박 수확 ==========")
            grasp_one_pumpkin(arm, target, grasp, motion_state)
            print("호박을 잡아 들어 올렸습니다.")
            deposit_in_bin(
                arm,
                bin_joints,
                camera_joints,
                motion_state,
            )
            harvested_count += 1
            print(f"[완료] 현재 적재 시도: {harvested_count}개")

        print(f"\n전체 수확·적재 동작이 끝났습니다: {harvested_count}개")

    except KeyboardInterrupt:
        print("\n사용자가 동작을 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if motion_state["holding"]:
                    print(
                        "경고: 그리퍼가 호박을 잡은 상태입니다. "
                        "호박을 받친 뒤 Enter를 누르세요."
                    )
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        pass
                    arm.open_gripper()
                    time.sleep(GRIPPER_WAIT_SEC)

                if calibration is not None:
                    print("저장된 카메라 자세로 돌아갑니다.")
                    arm.move_joints(
                        calibration["camera_joints"],
                        duration=movement_duration(140.0),
                    )
                print("정리 자세로 이동합니다.")
                arm.park()
            finally:
                arm.disconnect()
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
