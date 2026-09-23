#!/usr/bin/env python3
"""Automatically scan the full joint1 range, count pumpkins, and lift orange ones.

The folded camera pose sweeps every calibrated offset from -140 to +140
degrees. Detections are converted to fixed OMX-base XY coordinates and merged
across frames and views. Only clusters classified ORANGE are grasped. Each
orange pumpkin is lifted 30 mm, returned to its original location, and
released; this program has no bin/drop-off motion.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
import time

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
import omx_f.robot as omx_robot
from . import pumpkin_detected_approach_validation as base
from . import pumpkin_multiangle_approach_validation as multi
from vision_pkg.pumpkin_detection import color_classifier as hsv_filter
from vision_pkg.pumpkin_detection import yolo_detector
from . import pumpkin_orange_auto_grasp_validation as grasp


SCAN_OFFSETS_DEG = tuple(multi.ALLOWED_OFFSETS_DEG)
SCAN_FRAME_COUNT = 8
SCAN_FLUSH_FRAMES = 4
MIN_VIEW_HITS = 3
VIEW_MATCH_DISTANCE_M = 0.030
DUPLICATE_DISTANCE_M = 0.050
RESTORE_GRIPPER_DURATION_SEC = 3.0
AUTO_COUNTDOWN_SEC = 3


class ScanCancelled(Exception):
    """Raised when Q is pressed during the automatic scan."""


@dataclass
class Detection:
    target: dict
    label: str
    orange_ratio: float
    green_ratio: float
    confidence: float
    image_margin_px: float
    commanded_offset_deg: float
    measured_offset_deg: float

    @property
    def xy(self) -> np.ndarray:
        return np.asarray(self.target["world_target_xy"], dtype=float)


@dataclass
class ViewTrack:
    x: float
    y: float
    hits: int = 1
    detections: list[Detection] = field(default_factory=list)

    def add(self, detection: Detection) -> None:
        count = self.hits + 1
        self.x = (self.x * self.hits + float(detection.xy[0])) / count
        self.y = (self.y * self.hits + float(detection.xy[1])) / count
        self.hits = count
        self.detections.append(detection)

    def label(self) -> str:
        counts = Counter(item.label for item in self.detections)
        if not counts:
            return "UNKNOWN"
        ordered = counts.most_common()
        if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
            return "UNKNOWN"
        return ordered[0][0]

    def best_detection(self) -> Detection:
        majority = self.label()
        candidates = [d for d in self.detections if d.label == majority]
        if not candidates:
            candidates = list(self.detections)
        return max(
            candidates,
            key=lambda d: (
                d.orange_ratio if majority == "ORANGE" else d.green_ratio,
                d.image_margin_px,
                d.confidence,
            ),
        )


@dataclass
class PumpkinCluster:
    x: float
    y: float
    observations: list[Detection] = field(default_factory=list)

    def add_view(self, track: ViewTrack) -> None:
        views = len(self.observations)
        self.x = (self.x * views + track.x) / (views + 1)
        self.y = (self.y * views + track.y) / (views + 1)
        self.observations.append(track.best_detection())

    def label(self) -> str:
        counts = Counter(item.label for item in self.observations)
        orange = counts["ORANGE"]
        green = counts["GREEN"]
        unknown = counts["UNKNOWN"]
        if orange > green and orange > unknown:
            return "ORANGE"
        if green > orange and green > unknown:
            return "GREEN"
        return "UNKNOWN"

    def best_orange(self) -> Detection | None:
        candidates = [d for d in self.observations if d.label == "ORANGE"]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda d: (d.orange_ratio, d.image_margin_px, d.confidence),
        )


def require_start() -> None:
    print("\n이 프로그램은 각도 입력 없이 전 범위를 스캔한 뒤 자동으로 움직입니다.")
    print("주황 호박은 30mm 들어 올렸다가 같은 자리에 내려놓습니다.")
    print("사람·케이블을 치우고 로봇 주변을 완전히 비우세요.")
    while input("자동 스캔·집기를 시작하려면 START_AUTO 입력: ").strip() != "START_AUTO":
        print("START_AUTO를 정확히 입력해야 시작합니다.")


def normalized_gripper_value(arm) -> float:
    """Read and remember the gripper opening present at program start."""
    position = float(
        arm.bus.read(omx_robot.GRIPPER_ID, omx_robot.ct.PRESENT_POSITION)
    )
    denominator = float(arm.grip_open - arm.grip_closed)
    if abs(denominator) < 1.0:
        raise RuntimeError("그리퍼 열림·닫힘 보정 범위가 올바르지 않습니다.")
    value = (position - float(arm.grip_closed)) / denominator
    if not np.isfinite(value):
        raise RuntimeError("현재 기본 그리퍼 폭을 계산하지 못했습니다.")
    return min(1.0, max(0.0, float(value)))


def add_view_detection(tracks: list[ViewTrack], detection: Detection) -> None:
    nearest = None
    nearest_distance = float("inf")
    for track in tracks:
        distance = math.hypot(track.x - detection.xy[0], track.y - detection.xy[1])
        if distance < nearest_distance:
            nearest = track
            nearest_distance = distance
    if nearest is not None and nearest_distance <= VIEW_MATCH_DISTANCE_M:
        nearest.add(detection)
    else:
        tracks.append(
            ViewTrack(
                x=float(detection.xy[0]),
                y=float(detection.xy[1]),
                detections=[detection],
            )
        )


def add_global_track(clusters: list[PumpkinCluster], track: ViewTrack) -> None:
    nearest = None
    nearest_distance = float("inf")
    for cluster in clusters:
        distance = math.hypot(cluster.x - track.x, cluster.y - track.y)
        if distance < nearest_distance:
            nearest = cluster
            nearest_distance = distance
    if nearest is not None and nearest_distance <= DUPLICATE_DISTANCE_M:
        nearest.add_view(track)
    else:
        clusters.append(
            PumpkinCluster(
                x=track.x,
                y=track.y,
                observations=[track.best_detection()],
            )
        )


def detect_frame(
    model: YOLO,
    frame: np.ndarray,
    calibration,
    angle_residuals,
    commanded_offset_deg: float,
    measured_offset_deg: float,
):
    _, pumpkin_boxes = yolo_detector.detect_pumpkin_boxes(
        model,
        frame,
        confidence=base.CONFIDENCE,
        image_size=base.YOLO_IMAGE_SIZE,
        target_names=base.TARGET_CLASS_NAMES,
    )
    display = frame.copy()
    boundary = cv2.convexHull(
        calibration["image_points"].astype(np.int32).reshape(-1, 1, 2)
    )
    cv2.polylines(display, [boundary], True, (255, 255, 0), 2)
    detections: list[Detection] = []

    for box in pumpkin_boxes:
        xyxy = box.xyxy
        x1, y1, x2, y2 = hsv_filter.clamp_box(
            xyxy, frame.shape[1], frame.shape[0]
        )
        u = (float(xyxy[0]) + float(xyxy[2])) / 2.0
        v = (float(xyxy[1]) + float(xyxy[3])) / 2.0
        inside, margin_px = base.inside_hull((u, v), calibration["image_points"])
        colour = hsv_filter.classify_pumpkin_hsv(frame, xyxy)
        label = colour["label"]
        draw_colour = hsv_filter.label_color(label)
        cv2.rectangle(display, (x1, y1), (x2, y2), draw_colour, 2)
        cv2.putText(
            display,
            f"{label} O:{colour['orange_ratio'] * 100:.0f}% "
            f"G:{colour['green_ratio'] * 100:.0f}%",
            (x1, max(22, y1 - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            draw_colour,
            2,
            cv2.LINE_AA,
        )
        if not inside:
            continue
        try:
            target = multi.build_rotated_target(
                calibration,
                (u, v),
                commanded_offset_deg,
                measured_offset_deg,
                angle_residuals,
            )
        except (ValueError, RuntimeError):
            cv2.putText(
                display,
                "OUTSIDE CALIBRATION",
                (x1, min(frame.shape[0] - 8, y2 + 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )
            continue
        detections.append(
            Detection(
                target=target,
                label=label,
                orange_ratio=float(colour["orange_ratio"]),
                green_ratio=float(colour["green_ratio"]),
                confidence=box.confidence,
                image_margin_px=float(margin_px),
                commanded_offset_deg=float(commanded_offset_deg),
                measured_offset_deg=float(measured_offset_deg),
            )
        )
    return display, detections


def observe_angle(
    model,
    cap,
    calibration,
    angle_residuals,
    commanded_offset_deg,
    measured_offset_deg,
):
    tracks: list[ViewTrack] = []
    for _ in range(SCAN_FLUSH_FRAMES):
        cap.read()
    for frame_index in range(SCAN_FRAME_COUNT):
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("팔 카메라 프레임을 읽지 못했습니다.")
        display, detections = detect_frame(
            model,
            frame,
            calibration,
            angle_residuals,
            commanded_offset_deg,
            measured_offset_deg,
        )
        for detection in detections:
            add_view_detection(tracks, detection)
        cv2.putText(
            display,
            f"AUTO SCAN {commanded_offset_deg:+.0f} deg "
            f"{frame_index + 1}/{SCAN_FRAME_COUNT}",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            "Q: cancel automatic scan",
            (12, display.shape[0] - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Pumpkin full auto scan", display)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            raise ScanCancelled
    return [track for track in tracks if track.hits >= MIN_VIEW_HITS]


def print_summary(clusters: list[PumpkinCluster]) -> list[PumpkinCluster]:
    ripe = []
    counts = Counter(cluster.label() for cluster in clusters)
    print("\n========== 자동 전 범위 스캔 결과 ==========")
    print(f"중복 제거 전체 호박: {len(clusters)}개")
    print(f"주황(수확 대상): {counts['ORANGE']}개")
    print(f"초록(수확 제외): {counts['GREEN']}개")
    print(f"불확실(안전상 제외): {counts['UNKNOWN']}개")
    for index, cluster in enumerate(clusters, start=1):
        label = cluster.label()
        offsets = sorted(
            {int(round(item.commanded_offset_deg)) for item in cluster.observations}
        )
        print(
            f"{index:02d}. {label:7s} "
            f"XY=({cluster.x:+.4f}, {cluster.y:+.4f}) m "
            f"관측각={offsets}"
        )
        if label == "ORANGE" and cluster.best_orange() is not None:
            ripe.append(cluster)
    print("============================================")
    return ripe


def make_original_height_target(target: dict) -> dict:
    """Build approach stages from the saved grasp z with no extra height bias."""
    grasp_z = float(target["planned_grasp_z"])
    x, y = (float(value) for value in target["world_target_xy"])
    result = dict(target)
    result["xyz_stages"] = [
        np.asarray([x, y, grasp_z + clearance], dtype=float)
        for clearance in grasp.APPROACH_CLEARANCES_M
    ]
    return result


def harvest_one(
    arm,
    calibration,
    cluster: PumpkinCluster,
    default_gripper_value: float,
    harvest_index: int,
    harvest_total: int,
):
    observation = cluster.best_orange()
    if observation is None:
        return False
    target = make_original_height_target(observation.target)
    current_joints = np.asarray(arm.joints(), dtype=float)
    try:
        prealign, prealign_delta, joints_stages, _deltas = (
            multi.plan_fixed_pose_stages_from_folded_pose(
                arm,
                target["xyz_stages"],
                current_joints,
                calibration["pitch_rad"],
                calibration["roll_rad"],
            )
        )
    except (ValueError, RuntimeError) as error:
        print(f"[수확 건너뜀] {harvest_index}번 IK 실패: {error}")
        return False

    print(
        f"\n[자동 수확 {harvest_index}/{harvest_total}] "
        f"XY=({target['world_target_xy'][0]:+.4f}, "
        f"{target['world_target_xy'][1]:+.4f}) m / "
        f"집기 z={target['planned_grasp_z']:+.4f} m"
    )
    arm.move_joints(prealign, duration=multi.movement_duration(prealign_delta))
    arm.move_joints(joints_stages[0], duration=grasp.HIGH_MOVE_DURATION_SEC)
    current_stage = 0
    for index in (1, 2, 3):
        arm.move_joints(joints_stages[index], duration=grasp.LOWER_MOVE_DURATION_SEC)
        current_stage = index

    arm.close_gripper(
        duration=grasp.GRIPPER_CLOSE_DURATION_SEC,
        stall_guard=True,
        wait=True,
    )
    arm.move_joints(joints_stages[2], duration=grasp.LIFT_STEP_DURATION_SEC)
    current_stage = 2
    arm.move_joints(joints_stages[1], duration=grasp.LIFT_STEP_DURATION_SEC)
    current_stage = 1
    print("30mm 상승 완료.")
    time.sleep(2.0)

    arm.move_joints(joints_stages[2], duration=grasp.LIFT_STEP_DURATION_SEC)
    current_stage = 2
    arm.move_joints(joints_stages[3], duration=grasp.LIFT_STEP_DURATION_SEC)
    current_stage = 3
    arm.open_gripper(
        duration=grasp.GRIPPER_OPEN_DURATION_SEC,
        stall_guard=True,
        wait=True,
    )
    grasp.retreat_to_central(
        arm,
        calibration,
        prealign,
        joints_stages,
        current_stage,
    )
    arm.gripper(
        default_gripper_value,
        duration=RESTORE_GRIPPER_DURATION_SEC,
        stall_guard=False,
        wait=True,
    )
    print("원위치 복귀 및 시작 시 기본 그리퍼 폭 복원 완료.")
    return True


def main() -> None:
    arm = None
    cap = None
    calibration = None
    safe_to_park = False
    current_scan_offset = 0.0

    try:
        calibration = base.load_calibrations()
        angle_residuals = multi.load_angle_residuals()
        missing = [angle for angle in SCAN_OFFSETS_DEG if angle not in angle_residuals]
        if missing:
            formatted = ", ".join(f"{angle:+d}" for angle in missing)
            raise ValueError(
                "자동 수확에 필요한 각도별 XY 보정이 없습니다: " + formatted
            )
        model_path = base.find_model_path()
        print(f"YOLO 모델: {model_path}")
        model = YOLO(str(model_path))
        base.validate_model(model)
        cap = base.open_camera()
        require_start()

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)
        default_gripper_value = normalized_gripper_value(arm)
        print(f"시작 시 기본 그리퍼 폭 저장: {default_gripper_value:.3f}")

        camera_joints = calibration["camera_joints"]
        base_joint1_deg = float(np.degrees(camera_joints[0]))
        arm.move_joints(camera_joints, duration=base.CAMERA_MOVE_DURATION_SEC)
        time.sleep(base.SETTLE_TIME_SEC)
        safe_to_park = True

        clusters: list[PumpkinCluster] = []
        for commanded in SCAN_OFFSETS_DEG:
            target_joint1_deg = base_joint1_deg + commanded
            if abs(target_joint1_deg) > multi.JOINT1_SAFE_LIMIT_DEG:
                print(f"[스캔 건너뜀] {commanded:+d}도: joint1 안전 범위 밖")
                continue
            view_joints = camera_joints.copy()
            view_joints[0] = np.radians(target_joint1_deg)
            delta = commanded - current_scan_offset
            print(f"\n[자동 스캔] offset {commanded:+d}도로 이동")
            safe_to_park = False
            arm.move_joints(view_joints, duration=multi.movement_duration(delta))
            current_scan_offset = float(commanded)
            time.sleep(base.SETTLE_TIME_SEC)
            measured = np.asarray(arm.joints(), dtype=float)
            measured_offset = float(np.degrees(measured[0])) - base_joint1_deg
            tracks = observe_angle(
                model,
                cap,
                calibration,
                angle_residuals,
                float(commanded),
                measured_offset,
            )
            print(f"{commanded:+d}도 안정 검출: {len(tracks)}개")
            for track in tracks:
                add_global_track(clusters, track)

        print("\n전 범위 스캔 완료. 중앙 접힘 자세로 복귀합니다.")
        arm.move_joints(
            camera_joints,
            duration=multi.movement_duration(current_scan_offset),
        )
        current_scan_offset = 0.0
        safe_to_park = True
        cap.release()
        cap = None
        cv2.destroyAllWindows()

        ripe_clusters = print_summary(clusters)
        if not ripe_clusters:
            print("수확 가능한 주황 호박이 없습니다.")
            return
        ripe_clusters.sort(key=lambda c: math.hypot(c.x, c.y))
        print(f"{AUTO_COUNTDOWN_SEC}초 후 주황 호박 자동 집기를 시작합니다.")
        for remaining in range(AUTO_COUNTDOWN_SEC, 0, -1):
            print(f"자동 집기 시작까지 {remaining}초")
            time.sleep(1.0)

        successes = 0
        for index, cluster in enumerate(ripe_clusters, start=1):
            safe_to_park = False
            harvested = harvest_one(
                arm,
                calibration,
                cluster,
                default_gripper_value,
                index,
                len(ripe_clusters),
            )
            # harvest_one returns only after staying at, or returning to, the
            # calibrated central folded pose. Exceptions keep this flag false.
            safe_to_park = True
            if harvested:
                successes += 1
        print(
            f"\n자동 집기 검증 완료: 주황 {len(ripe_clusters)}개 중 "
            f"{successes}개 성공"
        )

    except ScanCancelled:
        print("사용자가 자동 스캔을 취소했습니다. 수확하지 않습니다.")
        if arm is not None and calibration is not None:
            arm.move_joints(
                calibration["camera_joints"],
                duration=multi.movement_duration(current_scan_offset),
            )
            safe_to_park = True
    except KeyboardInterrupt:
        safe_to_park = False
        print("\n사용자가 중단했습니다. 자동 추가 이동을 생략합니다.")
        print("로봇과 호박을 직접 받치고 상태를 확인하세요.")
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
                    print("자동 정리 자세를 생략합니다. 로봇 상태를 직접 확인하세요.")
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")
                print("로봇팔 연결을 종료했습니다.")


if __name__ == "__main__":
    main()
