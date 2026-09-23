"""A/B 호박 중심 5 cm 위까지만 이동하는 안전 접근 위치 검증."""

import json
import select
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower


TEST_DIR = Path(__file__).resolve().parent
SRC_ROOT = TEST_DIR.parents[1]
POSES_PATH = TEST_DIR / "pumpkin_ab_view_poses.json"
XY_PATH = TEST_DIR / "pumpkin_ab_grasp_xy_calibration.json"
PLANE_PATH = TEST_DIR / "pumpkin_plane_calibration.json"
MODEL_PATH = SRC_ROOT / "vision_pkg/models/nil_pumpkin.pt"
REQUIRED_FILES = (POSES_PATH, XY_PATH, PLANE_PATH, MODEL_PATH)

CONFIDENCE = 0.70
YOLO_IMAGE_SIZE = 416
TARGET_CLASS_NAMES = {"nil_pumpkin", "pumpkin"}
VIEW_MOVE_SEC = 8.0
APPROACH_MOVE_SEC = 8.0
SETTLE_SEC = 2.0
STABLE_FRAMES = 20
MAX_CENTER_JUMP_PX = 12.0
WINDOW = "Pumpkin A/B safe approach - Q cancel"


def check_required_files():
    missing = [path for path in REQUIRED_FILES if not path.is_file()]
    if not missing:
        return True
    print("필수 파일이 없습니다:", file=sys.stderr)
    for path in missing:
        print(f"  - {path}", file=sys.stderr)
    return False


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON 파일을 읽을 수 없습니다: {path}\n{exc}") from exc


def checked_array(value, shape, name):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} 값이 올바르지 않습니다: shape={array.shape}")
    return array


def choose_zone():
    while True:
        zone = input("테스트할 구역을 입력하세요 (A 또는 B): ").strip().upper()
        if zone in {"A", "B"}:
            return zone
        print("A 또는 B만 입력할 수 있습니다.")


def load_settings(zone):
    poses = read_json(POSES_PATH)
    xy_data = read_json(XY_PATH)
    plane = read_json(PLANE_PATH)
    try:
        camera = poses["camera"]
        grasp = plane["grasp"]
        settings = {
            "camera_index": int(camera["index"]),
            "width": int(camera["width"]),
            "height": int(camera["height"]),
            "zone_joints": checked_array(
                poses["zones"][zone]["joints_rad"],
                (5,), f"zones.{zone}.joints_rad",
            ),
            "homography": checked_array(
                xy_data["zones"][zone]["homography_pixel_uv_to_robot_xy"],
                (3, 3), f"zones.{zone}.homography_pixel_uv_to_robot_xy",
            ),
            "grasp_z": float(grasp["grasp_z_m"]),
            "approach_z": float(grasp["approach_z_m"]),
            "tool_pitch": float(grasp["tool_pitch_rad"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"보정 JSON 구조 또는 값이 올바르지 않습니다: {exc}") from exc
    scalars = (settings["grasp_z"], settings["approach_z"], settings["tool_pitch"])
    if not np.all(np.isfinite(scalars)):
        raise ValueError("grasp 높이 또는 tool pitch 값이 유한하지 않습니다.")
    clearance = settings["approach_z"] - settings["grasp_z"]
    if clearance < 0.05 - 1e-6:
        raise ValueError(
            "approach_z_m이 grasp_z_m보다 5 cm 이상 높지 않아 이동을 금지합니다. "
            f"높이 차이={clearance:.4f} m"
        )
    if settings["width"] <= 0 or settings["height"] <= 0:
        raise ValueError("카메라 해상도는 양수여야 합니다.")
    return settings


def open_camera(settings):
    cap = cv2.VideoCapture(settings["camera_index"], cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        raise RuntimeError(f"카메라 /dev/video{settings['camera_index']}를 열 수 없습니다.")
    for _ in range(8):
        cap.read()
    return cap


def normalize_name(value):
    return str(value).strip().lower()


def validate_model(model):
    names = model.names.values() if isinstance(model.names, dict) else model.names
    if not {normalize_name(name) for name in names}.intersection(TARGET_CLASS_NAMES):
        raise ValueError(f"모델에 호박 클래스가 없습니다: model.names={model.names}")


def detect_targets(model, frame):
    result = model.predict(
        source=frame, conf=CONFIDENCE, imgsz=YOLO_IMAGE_SIZE,
        device="cpu", verbose=False,
    )[0]
    targets = []
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())
        if (normalize_name(model.names[class_id]) not in TARGET_CLASS_NAMES
                or confidence < CONFIDENCE):
            continue
        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        targets.append({
            "u": (x1 + x2) / 2.0,
            "v": (y1 + y2) / 2.0,
            "confidence": confidence,
        })
    return result, targets


def window_closed():
    try:
        return cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True


def capture_stable_center(model, cap, zone):
    samples = []
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    print("화면에 호박을 정확히 한 개만 보여 주세요. Q를 누르면 취소합니다.")
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")
        result, targets = detect_targets(model, frame)
        annotated = result.plot()  # YOLO 박스만 표시하고 보정 영역은 그리지 않는다.
        if len(targets) != 1:
            samples.clear()
            status, color = "Show exactly ONE pumpkin", (0, 0, 255)
        else:
            target = targets[0]
            if samples:
                median_u = float(np.median([item["u"] for item in samples]))
                median_v = float(np.median([item["v"] for item in samples]))
                if np.hypot(target["u"] - median_u, target["v"] - median_v) > MAX_CENTER_JUMP_PX:
                    samples.clear()
                    print("검출 중심이 크게 흔들려 안정화 샘플을 초기화합니다.")
            samples.append(target)
            status, color = f"Stabilizing {len(samples)}/{STABLE_FRAMES}", (0, 255, 255)
            cv2.circle(annotated, (round(target["u"]), round(target["v"])), 6,
                       (0, 255, 255), -1)
        cv2.putText(annotated, f"Zone {zone} | {status}", (15, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.68, color, 2)
        cv2.putText(annotated, "Q: cancel and park", (15, annotated.shape[0] - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 255), 2)
        cv2.imshow(WINDOW, annotated)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")) or window_closed():
            return None, annotated
        if len(samples) >= STABLE_FRAMES:
            stable = {
                key: float(np.median([item[key] for item in samples]))
                for key in ("u", "v", "confidence")
            }
            return stable, annotated


def pixel_to_robot(u, v, homography):
    pixel = np.array([u, v, 1.0], dtype=float)
    mapped = homography @ pixel
    denominator = float(mapped[2])
    if not np.isfinite(denominator) or abs(denominator) < 1e-9:
        raise ValueError(f"픽셀 변환 분모가 0에 가까워 이동할 수 없습니다: {denominator}")
    x, y = float(mapped[0] / denominator), float(mapped[1] / denominator)
    if not np.all(np.isfinite([x, y])):
        raise ValueError("계산된 로봇 XY 좌표가 유한하지 않습니다.")
    return x, y


def summary_frame(frame, zone, target, x, y, z):
    display = frame.copy()
    lines = (
        f"Zone: {zone}", f"Pixel: ({target['u']:.1f}, {target['v']:.1f})",
        f"Robot XY: ({x:.4f}, {y:.4f}) m", f"Approach Z: {z:.4f} m",
        f"YOLO confidence: {target['confidence']:.3f}",
        "Terminal: type MOVE | Q: cancel",
    )
    for index, line in enumerate(lines):
        color = (0, 255, 0) if index < 5 else (0, 0, 255)
        cv2.putText(display, line, (15, 32 + index * 31),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2)
    cv2.imshow(WINDOW, display)
    cv2.waitKey(1)
    return display


def terminal_input_with_q(prompt, display):
    """터미널 입력을 기다리는 동안에도 영상 창의 Q를 처리한다."""
    print(prompt, end="", flush=True)
    while True:
        cv2.imshow(WINDOW, display)
        key = cv2.waitKey(50) & 0xFF
        if key in (ord("q"), ord("Q")) or window_closed():
            print("\n영상 창에서 취소했습니다.")
            return None
        readable, _, _ = select.select([sys.stdin], [], [], 0.0)
        if readable:
            line = sys.stdin.readline()
            return "" if line == "" else line.rstrip("\r\n")


def main():
    arm = None
    cap = None
    try:
        if not check_required_files():
            return 1
        zone = choose_zone()
        settings = load_settings(zone)
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        print("YOLO 클래스:", model.names)
        cap = open_camera(settings)

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        print("ready 자세로 이동합니다.")
        arm.ready(duration=5.0)
        print(f"[{zone} 구역] 저장된 촬영 자세로 이동합니다.")
        arm.move_joints(settings["zone_joints"], duration=VIEW_MOVE_SEC)
        print(f"카메라 안정화를 위해 {SETTLE_SEC:.1f}초 기다립니다.")
        time.sleep(SETTLE_SEC)

        target, annotated = capture_stable_center(model, cap, zone)
        if target is None:
            print("접근 테스트를 취소했습니다. 이동하지 않습니다.")
            return 0
        target_x, target_y = pixel_to_robot(
            target["u"], target["v"], settings["homography"]
        )
        approach_z = settings["approach_z"]  # grasp_z_m은 이동에 사용하지 않는다.
        print("\n========== 안전 접근 목표 ==========")
        print(f"선택 구역: {zone}")
        print(f"호박 중심 픽셀 (u, v): ({target['u']:.2f}, {target['v']:.2f})")
        print(f"계산된 로봇 좌표 (x, y): ({target_x:.4f}, {target_y:.4f}) m")
        print(f"접근 높이 z: {approach_z:.4f} m")
        print(f"YOLO confidence: {target['confidence']:.3f} (기준 {CONFIDENCE:.2f})")
        print("grasp_z_m 하강과 그리퍼 닫기는 비활성화되어 있습니다.")
        print("====================================")
        display = summary_frame(
            annotated, zone, target, target_x, target_y, approach_z
        )
        answer = terminal_input_with_q(
            "이동하려면 정확히 MOVE를 입력하세요: ", display
        )
        if answer != "MOVE":
            print("이동을 취소했습니다. 정리 자세로 이동합니다.")
            return 0
        try:
            arm.move_to(
                target_x, target_y, approach_z,
                duration=APPROACH_MOVE_SEC,
                pitch=settings["tool_pitch"], roll=0.0,
            )
        except ValueError as exc:
            print(f"역기구학 오류: {exc}", file=sys.stderr)
            print("다른 자세로 재시도하지 않고 안전하게 종료합니다.")
            return 1
        confirmation = terminal_input_with_q(
            "그리퍼가 호박 중심 위에 있는지 확인하고 Enter를 누르세요.", display
        )
        if confirmation is None:
            return 0
        print(f"[{zone} 구역] 촬영 자세로 복귀합니다.")
        arm.move_joints(settings["zone_joints"], duration=VIEW_MOVE_SEC)
        return 0
    except KeyboardInterrupt:
        print("\n사용자가 Ctrl+C로 중단했습니다.")
        return 130
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        if arm is not None:
            try:
                print("park() 정리 자세로 이동합니다.")
                arm.park()
            except Exception as exc:
                print(f"park() 중 오류: {exc}", file=sys.stderr)
            finally:
                try:
                    arm.disconnect()
                    print("로봇팔 연결을 종료했습니다.")
                except Exception as exc:
                    print(f"disconnect() 중 오류: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
