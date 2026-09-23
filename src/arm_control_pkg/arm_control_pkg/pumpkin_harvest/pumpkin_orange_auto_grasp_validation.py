#!/usr/bin/env python3
"""Grasp one pumpkin from a calibrated scan angle and lift it 30 mm.

The operator selects one calibrated joint1 scan offset. Detection is performed
in that folded scan pose, the saved per-angle XY residual is applied, and IK is
planned immediately without first returning to the central pose. The arm then
grasps one pumpkin, lifts it only 30 mm, returns it to the same spot, releases
it, and retreats safely. There is no bin transport.
"""

from __future__ import annotations

from collections import deque
import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from . import pumpkin_detected_approach_validation as base
from . import pumpkin_multiangle_approach_validation as multi
from . import pumpkin_orange_hsv_filter as hsv_filter


APPROACH_CLEARANCES_M = (0.080, 0.030, 0.010, 0.000)
# Keep the gripper 5 mm above the previously calibrated grasp height so the
# fingers do not scrape the table while closing.
GRASP_HEIGHT_BIAS_M = 0.005
GRIPPER_OPEN_DURATION_SEC = 3.0
GRIPPER_CLOSE_DURATION_SEC = 4.0
HIGH_MOVE_DURATION_SEC = 12.0
LOWER_MOVE_DURATION_SEC = 8.0
LIFT_STEP_DURATION_SEC = 6.0
RETURN_DURATION_SEC = 12.0


class TestCancelled(Exception):
    """Raised when the operator cancels before target motion."""


def choose_orange_pumpkin(model: YOLO, cap, calibration):
    """Automatically lock one stable ORANGE pumpkin; reject green/unknown."""
    window = "ORANGE auto harvest - Q cancel"
    history = deque(maxlen=base.STABLE_SAMPLE_COUNT)
    boundary = cv2.convexHull(
        calibration["image_points"].astype(np.int32).reshape(-1, 1, 2)
    )
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    print("\n청록색 보정 영역 안에서 주황 호박 하나를 찾습니다.")
    print("GREEN·UNKNOWN은 수확하지 않습니다.")
    print("ORANGE 좌표가 안정되면 별도 입력 없이 자동으로 수확을 시작합니다.")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("팔 카메라 프레임을 읽지 못했습니다.")
        if frame.shape[:2] != (base.CAMERA_HEIGHT, base.CAMERA_WIDTH):
            raise RuntimeError(
                f"영상 크기가 {frame.shape[1]}x{frame.shape[0]}입니다. "
                f"필요한 크기는 {base.CAMERA_WIDTH}x{base.CAMERA_HEIGHT}입니다."
            )

        result = model.predict(
            source=frame,
            conf=base.CONFIDENCE,
            imgsz=base.YOLO_IMAGE_SIZE,
            device="cpu",
            verbose=False,
        )[0]
        annotated = frame.copy()
        cv2.polylines(annotated, [boundary], True, (255, 255, 0), 2)
        orange_candidates = []
        counts = {"ORANGE": 0, "GREEN": 0, "UNKNOWN": 0}

        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = base.normalize_name(model.names[class_id])
            if class_name not in base.TARGET_CLASS_NAMES:
                continue

            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = hsv_filter.clamp_box(
                xyxy, frame.shape[1], frame.shape[0]
            )
            u = (float(xyxy[0]) + float(xyxy[2])) / 2.0
            v = (float(xyxy[1]) + float(xyxy[3])) / 2.0
            inside, margin_px = base.inside_hull(
                (u, v), calibration["image_points"]
            )
            colour = hsv_filter.classify_pumpkin_hsv(frame, xyxy)
            label = colour["label"]
            counts[label] += 1
            draw_color = hsv_filter.label_color(label)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), draw_color, 2)
            left, top, right, bottom = colour["body_box"]
            cv2.rectangle(
                annotated, (left, top), (right, bottom), (255, 255, 255), 1
            )
            cv2.putText(
                annotated,
                f"{label} O:{colour['orange_ratio'] * 100:.0f}% "
                f"G:{colour['green_ratio'] * 100:.0f}%",
                (x1, max(22, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                draw_color,
                2,
                cv2.LINE_AA,
            )

            if label == "ORANGE" and inside:
                orange_candidates.append(
                    {
                        "u": u,
                        "v": v,
                        "confidence": float(box.conf[0].item()),
                        "margin_px": margin_px,
                    }
                )

        stable_selected = None
        if len(orange_candidates) != 1:
            history.clear()
            if len(orange_candidates) == 0:
                status = "NO ORANGE TARGET - harvest blocked"
            else:
                status = f"Need 1 orange target (now {len(orange_candidates)})"
            status_color = (0, 0, 255)
        else:
            detection = orange_candidates[0]
            history.append(detection)
            point = (int(round(detection["u"])), int(round(detection["v"])))
            cv2.drawMarker(
                annotated, point, (0, 0, 255), cv2.MARKER_CROSS, 24, 2
            )
            selected = base.stable_pixel(history)
            if selected is None:
                status = (
                    f"ORANGE stabilizing {len(history)}/{base.STABLE_SAMPLE_COUNT}"
                )
                status_color = (0, 165, 255)
            else:
                status = "ORANGE STABLE - AUTO LOCK"
                status_color = (0, 255, 0)
                stable_selected = selected

        cv2.putText(
            annotated,
            status,
            (15, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            status_color,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            f"O:{counts['ORANGE']} G:{counts['GREEN']} U:{counts['UNKNOWN']}",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow(window, annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            return None
        if stable_selected is not None:
            print("HSV 판정 ORANGE 자동 확정: 수확 좌표를 계산합니다.")
            return stable_selected
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            return None


def make_full_grasp_target(target: dict) -> dict:
    grasp_z = float(target["planned_grasp_z"]) + GRASP_HEIGHT_BIAS_M
    x, y = (float(value) for value in target["world_target_xy"])
    result = dict(target)
    result["original_planned_grasp_z"] = float(target["planned_grasp_z"])
    result["planned_grasp_z"] = grasp_z
    result["xyz_stages"] = [
        np.asarray([x, y, grasp_z + clearance], dtype=float)
        for clearance in APPROACH_CLEARANCES_M
    ]
    return result


def print_plan(
    target,
    commanded_offset_deg,
    measured_offset_deg,
    calibration,
    current_joints,
    prealign_joints,
    prealign_delta_deg,
    joints_stages,
    deltas,
):
    print("\n========== 다각도 단일 집기·30mm 상승 계획 ==========")
    print(
        f"촬영각: 명령 {commanded_offset_deg:+.0f}도 / "
        f"실측 {measured_offset_deg:+.2f}도"
    )
    print(f"검출 기준: {base.TARGET_PIXEL_MODE}")
    print(
        f"안정화 픽셀: u={target['pixel'][0]:.1f}, "
        f"v={target['pixel'][1]:.1f}"
    )
    print(
        "각도별 로컬 잔여보정: "
        f"dx={target['residual_local'][0] * 1000:+.1f} mm, "
        f"dy={target['residual_local'][1] * 1000:+.1f} mm"
    )
    print(
        "최종 목표 XY [m]: "
        f"x={target['world_target_xy'][0]:.4f}, "
        f"y={target['world_target_xy'][1]:.4f}"
    )
    print(f"계산 바닥 z: {target['floor_z']:.4f} m")
    print(
        "바닥 긁힘 방지 집기 z: "
        f"{target['planned_grasp_z']:.4f} m "
        f"(기존 계획보다 +{GRASP_HEIGHT_BIAS_M * 1000:.0f} mm)"
    )
    print(f"고정 pitch: {np.degrees(calibration['pitch_rad']):.1f}도")
    print(f"현재 관절 [deg]: {np.round(np.degrees(current_joints), 1)}")
    print(
        "수확방향 사전정렬 관절 [deg]: "
        f"{np.round(np.degrees(prealign_joints), 1)}"
    )
    print(f"접힌 자세 joint1 사전정렬 변화: {prealign_delta_deg:.1f}도")

    for index, (clearance, xyz, joints, delta) in enumerate(
        zip(
            APPROACH_CLEARANCES_M,
            target["xyz_stages"],
            joints_stages,
            deltas,
        ),
        start=1,
    ):
        delta_deg, max_delta, _total_delta = delta
        label = (
            "계획 집기 높이"
            if clearance == 0.0
            else f"집기점 +{clearance * 1000:.0f}mm"
        )
        print(f"단계 {index}: {label} / XYZ={np.round(xyz, 4)}")
        print(f"  관절 [deg]: {np.round(np.degrees(joints), 1)}")
        print(
            f"  이전 자세 대비 변화 [deg]: {np.round(delta_deg, 1)} "
            f"(최대 {max_delta:.1f}도)"
        )

    print("그리퍼: 전류 제한을 사용해 완전히 닫기")
    print("상승: 동일 XY에서 0→10→30mm, 이후 같은 자리에 내려놓기")
    print("수평 이동·적재 없음")
    print("====================================================")


def retreat_to_central(
    arm,
    calibration,
    prealign_joints,
    joints_stages,
    current_stage_index,
):
    """Retreat from the current stage to 80 mm, fold, then return central."""
    for index in range(current_stage_index - 1, -1, -1):
        clearance_mm = APPROACH_CLEARANCES_M[index] * 1000
        print(f"계획 집기점 +{clearance_mm:.0f} mm로 복귀합니다.")
        arm.move_joints(joints_stages[index], duration=LOWER_MOVE_DURATION_SEC)

    print("80mm 상공에서 수확방향 접힘 자세로 복귀합니다.")
    arm.move_joints(prealign_joints, duration=RETURN_DURATION_SEC)
    joint1_delta_deg = np.degrees(
        prealign_joints[0] - calibration["camera_joints"][0]
    )
    print("팔을 접은 상태에서 중앙 안전 자세로 복귀합니다.")
    arm.move_joints(
        calibration["camera_joints"],
        duration=multi.movement_duration(joint1_delta_deg),
    )


def main() -> None:
    arm = None
    cap = None
    calibration = None
    at_central_pose = False
    gripper_released = True

    try:
        calibration = base.load_calibrations()
        angle_residuals = multi.load_angle_residuals()
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()

        print("이 프로그램은 선택한 촬영각에서 주황 호박 하나를 자동으로 잡습니다.")
        print("HSV 판정이 GREEN 또는 UNKNOWN이면 접근·집기를 차단합니다.")
        print("30mm만 들었다가 같은 자리에 내려놓으며 적재하지 않습니다.")
        print("주의: 촬영 offset을 입력하면 중간 확인 명령 없이 자동 동작합니다.")
        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        print("중앙 보정 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=base.CAMERA_MOVE_DURATION_SEC)
        time.sleep(base.SETTLE_TIME_SEC)
        at_central_pose = True

        commanded_offset_deg = multi.ask_offset()
        if commanded_offset_deg is None:
            raise TestCancelled
        angle_key = int(round(commanded_offset_deg))
        if angle_key not in angle_residuals:
            raise ValueError(
                f"{angle_key:+d}도 XY 보정값이 없습니다. "
                "먼저 pumpkin_multiangle_xy_micro_adjust.py에서 SAVE하세요."
            )

        target_joint1_deg = base_joint1_deg + commanded_offset_deg
        if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
            raise ValueError(
                f"촬영 joint1={target_joint1_deg:.1f}도가 안전 한계 "
                f"±{multi.JOINT1_SAFE_LIMIT_DEG:.0f}도를 벗어납니다."
            )

        view_joints = camera_joints.copy()
        view_joints[0] = np.radians(target_joint1_deg)
        print(f"촬영 offset={commanded_offset_deg:+.0f}도로 이동합니다.")
        at_central_pose = False
        arm.move_joints(
            view_joints,
            duration=multi.movement_duration(commanded_offset_deg),
        )
        time.sleep(base.SETTLE_TIME_SEC)

        measured_joints = np.asarray(arm.joints(), dtype=float)
        measured_joint1_deg = float(np.degrees(measured_joints[0]))
        measured_offset_deg = measured_joint1_deg - base_joint1_deg
        print(
            f"실측 joint1={measured_joint1_deg:.2f}도 / "
            f"중앙 대비={measured_offset_deg:+.2f}도"
        )

        print("현재 촬영 화면에서 ORANGE 호박만 수확 대상으로 선택합니다.")
        selected = choose_orange_pumpkin(model, cap, calibration)
        cap.release()
        cap = None
        cv2.destroyAllWindows()
        if selected is None:
            raise TestCancelled

        try:
            target = multi.build_rotated_target(
                calibration,
                selected,
                commanded_offset_deg,
                measured_offset_deg,
                angle_residuals,
            )
            target = make_full_grasp_target(target)
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 베이스 기준 목표를 만들지 못했습니다: {error}")
            print("중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        print("현재 촬영 접힘 자세에서 바로 집기 IK를 계산합니다.")
        current_joints = np.asarray(arm.joints(), dtype=float)
        try:
            (
                prealign_joints,
                prealign_delta_deg,
                joints_stages,
                deltas,
            ) = multi.plan_fixed_pose_stages_from_folded_pose(
                arm,
                target["xyz_stages"],
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        except (ValueError, RuntimeError) as error:
            print(f"[이동 금지] 안전 IK를 만들지 못했습니다: {error}")
            print("중앙 자세로 복귀합니다.")
            arm.move_joints(
                camera_joints,
                duration=multi.movement_duration(measured_offset_deg),
            )
            at_central_pose = True
            return

        print_plan(
            target,
            commanded_offset_deg,
            measured_offset_deg,
            calibration,
            current_joints,
            prealign_joints,
            prealign_delta_deg,
            joints_stages,
            deltas,
        )

        print("사람·케이블을 치우세요. 3초 후 자동 수확 동작을 시작합니다.")
        for remaining in (3, 2, 1):
            print(f"자동 시작까지 {remaining}초")
            time.sleep(1.0)

        print("[자동] 접힌 채 수확방향으로 사전정렬합니다.")
        arm.move_joints(
            prealign_joints,
            duration=multi.movement_duration(prealign_delta_deg),
        )
        print("수확방향 사전정렬 완료. 팔은 접힌 자세입니다.")

        print("[자동] 80mm 상공으로 이동합니다.")
        arm.move_joints(joints_stages[0], duration=HIGH_MOVE_DURATION_SEC)
        current_stage = 0
        print("80mm 상공 도착.")

        print(
            "OPEN_GRIPPER 동작을 생략합니다. "
            "현재 기본 잡기 폭을 그대로 유지합니다."
        )
        print(
            "하강 전에 호박 몸통은 들어가고 넝쿨은 그리퍼 밖에 있는지 "
            "직접 확인하세요."
        )

        stages = (
            (1, "30mm 상공"),
            (2, "10mm 상공"),
            (3, "계획 집기 높이"),
        )
        for index, label in stages:
            print(f"[자동] {label}로 이동합니다.")
            arm.move_joints(
                joints_stages[index], duration=LOWER_MOVE_DURATION_SEC
            )
            current_stage = index
            print(f"{label} 도착. 아직 그리퍼는 열려 있습니다.")

        print("[자동] 전류 제한으로 호박을 잡습니다.")
        gripper_released = False
        arm.close_gripper(
            duration=GRIPPER_CLOSE_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        print("그리퍼 닫기 완료.")

        print("[자동] 동일 XY에서 10mm 상승합니다.")
        arm.move_joints(joints_stages[2], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 2
        print("[자동] 동일 XY에서 30mm 상승합니다.")
        arm.move_joints(joints_stages[1], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 1
        print("30mm 상승 완료. 수평 이동은 하지 않습니다.")
        time.sleep(2.0)

        print("[자동] 집기점보다 10mm 위로 하강합니다.")
        arm.move_joints(joints_stages[2], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 2
        print("[자동] 원래 집기 높이까지 하강합니다.")
        arm.move_joints(joints_stages[3], duration=LIFT_STEP_DURATION_SEC)
        current_stage = 3

        print("[자동] 호박을 놓기 위해 그리퍼를 엽니다.")
        arm.open_gripper(
            duration=GRIPPER_OPEN_DURATION_SEC,
            stall_guard=True,
            wait=True,
        )
        gripper_released = True
        print("그리퍼를 열었습니다. 호박은 원래 위치에 있습니다.")

        retreat_to_central(
            arm,
            calibration,
            prealign_joints,
            joints_stages,
            current_stage,
        )
        at_central_pose = True
        print("다각도 단일 집기·30mm 상승·원위치 복귀 검증이 끝났습니다.")

    except TestCancelled:
        print("목표 선택을 취소했습니다.")
        if arm is not None and calibration is not None and not at_central_pose:
            measured = np.asarray(arm.joints(), dtype=float)
            delta_deg = np.degrees(
                measured[0] - calibration["camera_joints"][0]
            )
            arm.move_joints(
                calibration["camera_joints"],
                duration=multi.movement_duration(delta_deg),
            )
            at_central_pose = True
    except KeyboardInterrupt:
        at_central_pose = False
        print("\n사용자가 중단했습니다. 자동 이동과 그리퍼 동작을 생략합니다.")
        print("호박을 들고 있다면 팔과 호박을 받쳐 직접 상태를 확인하세요.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if at_central_pose and gripper_released:
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "자동 정리 자세를 생략합니다. 로봇이 멈췄는지 확인하고 "
                        "그리퍼·호박 상태를 직접 확인하세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
