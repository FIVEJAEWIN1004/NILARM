"""Detect and pick exactly one pumpkin from a taught A/B camera view.

Camera joints are used only for measurement.  A separate grasp pitch is chosen
by non-moving IK checks before any pick motion.  Q or Ctrl-C cancels safely.
"""

import json
import math
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
XY_CALIBRATION_PATH = TEST_DIR / "pumpkin_ab_grasp_xy_calibration.json"
PLANE_CALIBRATION_PATH = TEST_DIR / "pumpkin_plane_calibration.json"
MODEL_PATH = SRC_ROOT / "vision_pkg/models/nil_pumpkin.pt"
REQUIRED_FILES = (
    POSES_PATH,
    XY_CALIBRATION_PATH,
    PLANE_CALIBRATION_PATH,
    MODEL_PATH,
)

CONFIDENCE = 0.70
YOLO_IMAGE_SIZE = 416
TARGET_CLASS_NAMES = {"nil_pumpkin", "pumpkin"}

CAMERA_MOVE_DURATION_SEC = 8.0
APPROACH_MOVE_DURATION_SEC = 8.0
DESCEND_MOVE_DURATION_SEC = 5.0
SETTLE_TIME_SEC = 2.0
STABLE_FRAME_COUNT = 20
STABLE_PIXEL_RADIUS = 12.0
GRIPPER_CLOSE_WAIT_SEC = 1.5
HOLD_AFTER_LIFT_SEC = 3.0
WINDOW_NAME = "Pumpkin A/B pick one - Q cancel"

GRASP_PITCH_CANDIDATES_DEG = [
    80.0,
    75.0,
    70.0,
    65.0,
    60.0,
    55.0,
    50.0,
    45.0,
]


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
    if array.shape != shape:
        raise ValueError(f"{name} 형태가 {shape}가 아닙니다: {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name}에 유한하지 않은 값이 있습니다.")
    return array


def choose_zone():
    while True:
        zone = input("테스트할 구역을 입력하세요 [A/B]: ").strip().upper()
        if zone in {"A", "B"}:
            return zone
        print("A 또는 B만 입력할 수 있습니다.")


def load_settings(zone):
    poses = read_json(POSES_PATH)
    xy_calibration = read_json(XY_CALIBRATION_PATH)
    plane_calibration = read_json(PLANE_CALIBRATION_PATH)
    try:
        camera = poses["camera"]
        zone_data = xy_calibration["zones"][zone]
        records = zone_data["records"]
        if not isinstance(records, list) or len(records) != 4:
            raise ValueError(
                f"zones.{zone}.records에는 정확히 네 보정점이 필요합니다."
            )
        calibration_pixels = checked_array(
            [record["pixel_uv"] for record in records],
            (4, 2),
            f"zones.{zone}.records[*].pixel_uv",
        )
        grasp = plane_calibration["grasp"]
        settings = {
            "camera_index": int(camera["index"]),
            "width": int(camera["width"]),
            "height": int(camera["height"]),
            "camera_joints": checked_array(
                poses["zones"][zone]["joints_rad"],
                (5,),
                f"zones.{zone}.joints_rad",
            ),
            "homography": checked_array(
                zone_data["homography_pixel_uv_to_robot_xy"],
                (3, 3),
                f"zones.{zone}.homography_pixel_uv_to_robot_xy",
            ),
            "calibration_pixels": calibration_pixels,
            "approach_z": float(grasp["approach_z_m"]),
            "grasp_z": float(grasp["grasp_z_m"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"보정 JSON 필드 또는 값 오류: {exc}") from exc

    if settings["width"] <= 0 or settings["height"] <= 0:
        raise ValueError("카메라 해상도는 양수여야 합니다.")
    if not np.all(np.isfinite([settings["approach_z"], settings["grasp_z"]])):
        raise ValueError("접근 또는 잡기 높이가 유한하지 않습니다.")
    if settings["approach_z"] <= settings["grasp_z"]:
        raise ValueError("approach_z_m은 grasp_z_m보다 높아야 합니다.")

    hull = cv2.convexHull(
        settings["calibration_pixels"].astype(np.float32)
    )
    if len(hull) < 3 or abs(cv2.contourArea(hull)) < 1.0:
        raise ValueError("선택 구역의 네 보정점이 유효한 영역을 만들지 못합니다.")
    settings["calibration_hull"] = hull
    return settings


def open_camera(settings):
    cap = cv2.VideoCapture(settings["camera_index"], cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        raise RuntimeError(
            f"카메라 /dev/video{settings['camera_index']}를 열 수 없습니다."
        )
    for _ in range(8):
        cap.read()
    return cap


def normalize_name(value):
    return str(value).strip().lower()


def validate_model(model):
    names = model.names.values() if isinstance(model.names, dict) else model.names
    available = {normalize_name(name) for name in names}
    if not available.intersection(TARGET_CLASS_NAMES):
        raise ValueError(
            "모델 클래스에 nil_pumpkin 또는 pumpkin이 없습니다. "
            f"model.names={model.names}"
        )


def detect_targets(model, frame):
    result = model.predict(
        source=frame,
        conf=CONFIDENCE,
        imgsz=YOLO_IMAGE_SIZE,
        device="cpu",
        verbose=False,
    )[0]
    targets = []
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())
        if normalize_name(model.names[class_id]) not in TARGET_CLASS_NAMES:
            continue
        if confidence < CONFIDENCE:
            continue
        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        targets.append(
            {
                "u": (x1 + x2) / 2.0,
                "v": (y1 + y2) / 2.0,
                "confidence": confidence,
            }
        )
    return result, targets


def window_closed():
    try:
        return cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True


def capture_stable_target(model, cap, zone):
    samples = []
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    print("화면에 호박을 정확히 한 개만 보여 주세요. Q를 누르면 취소합니다.")
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("카메라 프레임을 읽지 못했습니다.")
        result, targets = detect_targets(model, frame)
        annotated = result.plot()

        if len(targets) != 1:
            samples.clear()
            status = "Show exactly ONE pumpkin"
            color = (0, 0, 255)
        else:
            target = targets[0]
            if samples:
                median_u = float(np.median([item["u"] for item in samples]))
                median_v = float(np.median([item["v"] for item in samples]))
                jump = float(
                    np.hypot(target["u"] - median_u, target["v"] - median_v)
                )
                if jump > STABLE_PIXEL_RADIUS:
                    samples.clear()
                    print("검출 중심이 크게 흔들려 안정화 샘플을 초기화합니다.")
            samples.append(target)
            status = f"Stabilizing {len(samples)}/{STABLE_FRAME_COUNT}"
            color = (0, 255, 255)
            cv2.circle(
                annotated,
                (round(target["u"]), round(target["v"])),
                6,
                (0, 255, 255),
                -1,
            )

        cv2.putText(
            annotated,
            f"Zone {zone} | {status}",
            (15, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            color,
            2,
        )
        cv2.putText(
            annotated,
            "Q: cancel and park",
            (15, annotated.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 0, 255),
            2,
        )
        cv2.imshow(WINDOW_NAME, annotated)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")) or window_closed():
            return None, annotated
        if len(samples) >= STABLE_FRAME_COUNT:
            stable = {
                key: float(np.median([item[key] for item in samples]))
                for key in ("u", "v", "confidence")
            }
            return stable, annotated


def pixel_inside_calibration(u, v, hull):
    return cv2.pointPolygonTest(hull, (float(u), float(v)), False) >= 0


def pixel_to_robot(u, v, homography):
    pixel = np.array([u, v, 1.0], dtype=float)
    mapped = homography @ pixel
    denominator = float(mapped[2])
    if not np.isfinite(denominator) or abs(denominator) < 1e-9:
        raise ValueError(
            f"픽셀 변환 분모가 0에 가까워 이동할 수 없습니다: {denominator}"
        )
    x = float(mapped[0] / denominator)
    y = float(mapped[1] / denominator)
    if not np.all(np.isfinite([x, y])):
        raise ValueError("계산된 로봇 XY 좌표가 유한하지 않습니다.")
    return x, y


def nonmoving_checked_ik(arm, xyz, q_seed, pitch):
    """Calculate IK and validate library limits without commanding motors."""
    q = arm.kin.inverse(xyz, q_seed, pitch=pitch, roll=0.0)
    checked = arm.check_limits(q, current=q_seed)
    if not np.allclose(checked, q, rtol=0.0, atol=1e-9):
        raise ValueError("관절 한계 검사에서 IK 결과가 변경되었습니다.")
    if q.shape != (5,) or not np.all(np.isfinite(q)):
        raise ValueError("IK 결과 관절값이 올바르지 않습니다.")
    return q


def select_grasp_pitch(arm, x, y, approach_z, grasp_z):
    seed = np.asarray(arm.joints(), dtype=float)
    for pitch_deg in GRASP_PITCH_CANDIDATES_DEG:
        pitch = math.radians(pitch_deg)
        try:
            approach_q = nonmoving_checked_ik(
                arm, (x, y, approach_z), seed, pitch
            )
        except ValueError as exc:
            print(f"pitch {pitch_deg:.0f}°: 접근 불가능 ({exc})")
            continue
        try:
            nonmoving_checked_ik(
                arm, (x, y, grasp_z), approach_q, pitch
            )
        except ValueError as exc:
            print(f"pitch {pitch_deg:.0f}°: 접근 가능, 하강 불가능 ({exc})")
            continue
        print(f"pitch {pitch_deg:.0f}°: 접근/하강 가능")
        print(f"선택된 집기 pitch: {pitch_deg:.0f}°")
        return pitch, pitch_deg
    return None


def make_summary_frame(frame, zone, target, x, y, approach_z, grasp_z, pitch_deg):
    display = frame.copy()
    lines = (
        f"Zone: {zone}",
        f"Pixel: ({target['u']:.1f}, {target['v']:.1f})",
        f"Confidence: {target['confidence']:.3f}",
        f"Robot XY: ({x:.4f}, {y:.4f}) m",
        f"Z approach/grasp: {approach_z:.4f}/{grasp_z:.4f} m",
        f"Grasp pitch: {pitch_deg:.0f} deg",
        "Terminal confirmation required | Q: cancel",
    )
    for index, line in enumerate(lines):
        color = (0, 255, 0) if index < 6 else (0, 0, 255)
        cv2.putText(
            display,
            line,
            (15, 30 + index * 29),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            color,
            2,
        )
    cv2.imshow(WINDOW_NAME, display)
    cv2.waitKey(1)
    return display


def terminal_input_with_q(prompt, display):
    print(prompt, end="", flush=True)
    while True:
        cv2.imshow(WINDOW_NAME, display)
        key = cv2.waitKey(50) & 0xFF
        if key in (ord("q"), ord("Q")) or window_closed():
            print("\n영상 창에서 취소했습니다.")
            return None
        readable, _, _ = select.select([sys.stdin], [], [], 0.0)
        if readable:
            line = sys.stdin.readline()
            return "" if line == "" else line.rstrip("\r\n")


def cleanup_arm(arm, settings, motion):
    """Run independent best-effort recovery stages, then disconnect."""
    if motion["needs_lift"] or motion["holding"]:
        try:
            print("[정리] 현재 목표의 approach_z까지 상승을 시도합니다.")
            arm.move_to(
                motion["x"],
                motion["y"],
                settings["approach_z"],
                duration=DESCEND_MOVE_DURATION_SEC,
                pitch=motion["pitch"],
                roll=0.0,
                refine=0,
            )
            motion["needs_lift"] = False
        except Exception as exc:
            print(f"[정리 오류] 안전 높이 상승 실패: {exc}", file=sys.stderr)

    if motion["pick_started"] or motion["holding"]:
        try:
            print("[정리] 안전 높이에서 그리퍼 열기를 시도합니다.")
            arm.open_gripper()
            motion["holding"] = False
        except Exception as exc:
            print(f"[정리 오류] 그리퍼 열기 실패: {exc}", file=sys.stderr)

    if settings is not None and not motion["at_camera_pose"]:
        try:
            print("[정리] 선택 구역 촬영 자세로 복귀를 시도합니다.")
            arm.move_joints(
                settings["camera_joints"],
                duration=CAMERA_MOVE_DURATION_SEC,
            )
            motion["at_camera_pose"] = True
        except Exception as exc:
            print(f"[정리 오류] 촬영 자세 복귀 실패: {exc}", file=sys.stderr)

    try:
        print("[정리] park()를 시도합니다.")
        arm.park()
    except Exception as exc:
        print(f"[정리 오류] park() 실패: {exc}", file=sys.stderr)

    try:
        arm.disconnect()
        print("로봇팔 연결을 종료했습니다.")
    except Exception as exc:
        print(f"[정리 오류] disconnect() 실패: {exc}", file=sys.stderr)


def main():
    arm = None
    cap = None
    settings = None
    motion = {
        "x": None,
        "y": None,
        "pitch": None,
        "pick_started": False,
        "needs_lift": False,
        "holding": False,
        "at_camera_pose": False,
        "connected": False,
    }
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
        arm = OmxFollower()
        arm.connect()
        motion["connected"] = True
        arm.ready(duration=5.0)
        print(f"[{zone} 구역] 저장된 5관절 촬영 자세로 이동합니다.")
        arm.move_joints(
            settings["camera_joints"], duration=CAMERA_MOVE_DURATION_SEC
        )
        motion["at_camera_pose"] = True
        time.sleep(SETTLE_TIME_SEC)

        target, annotated = capture_stable_target(model, cap, zone)
        if target is None:
            print("사용자가 검출을 취소했습니다.")
            return 0
        if not pixel_inside_calibration(
            target["u"], target["v"], settings["calibration_hull"]
        ):
            print("호박이 보정 영역 밖에 있으므로 이동을 취소합니다.")
            return 1

        x, y = pixel_to_robot(
            target["u"], target["v"], settings["homography"]
        )
        approach_z = settings["approach_z"]
        grasp_z = settings["grasp_z"]
        selected = select_grasp_pitch(arm, x, y, approach_z, grasp_z)
        if selected is None:
            print("접근과 하강이 모두 가능한 pitch 후보가 없어 이동하지 않습니다.")
            return 1
        grasp_pitch, grasp_pitch_deg = selected

        distance = math.hypot(x, y)
        direction = math.atan2(y, x)
        print("\n========== 한 개 집기 목표 ==========")
        print(f"선택 구역: {zone}")
        print(f"YOLO 중심 픽셀 u, v: ({target['u']:.2f}, {target['v']:.2f})")
        print(f"YOLO confidence: {target['confidence']:.3f}")
        print(f"계산된 로봇 좌표 x, y: ({x:.4f}, {y:.4f}) m")
        print(f"접근 높이: {approach_z:.4f} m")
        print(f"잡기 높이: {grasp_z:.4f} m")
        print(f"선택된 grasp pitch: {grasp_pitch_deg:.0f}°")
        print(f"로봇 기준 거리 hypot(x, y): {distance:.4f} m")
        print(
            f"로봇 기준 방향 atan2(y, x): {direction:.4f} rad "
            f"({math.degrees(direction):.1f}°)"
        )
        print("이동로봇 본체를 움직이지 마세요.")
        print("로봇팔 주변을 비우고 비상 정지를 준비하세요.")
        print("=====================================")

        display = make_summary_frame(
            annotated, zone, target, x, y, approach_z, grasp_z, grasp_pitch_deg
        )
        answer = terminal_input_with_q(
            "집기를 시작하려면 정확히 PICK을 입력하세요: ", display
        )
        if answer != "PICK":
            print("집기를 취소했습니다. 촬영 자세를 거쳐 정리합니다.")
            return 0

        motion.update(
            {
                "x": x,
                "y": y,
                "pitch": grasp_pitch,
                "pick_started": True,
                "at_camera_pose": False,
            }
        )
        print("[집기] 그리퍼를 엽니다.")
        arm.open_gripper()
        print("[집기] 별도로 선택한 pitch로 접근 높이까지 이동합니다.")
        arm.move_to(
            x,
            y,
            approach_z,
            duration=APPROACH_MOVE_DURATION_SEC,
            pitch=grasp_pitch,
            roll=0.0,
            refine=0,
        )

        answer = terminal_input_with_q(
            "그리퍼가 호박 중심 위에 있으면 LOWER를 입력하세요: ", display
        )
        if answer != "LOWER":
            print("하강을 취소했습니다. 촬영 자세를 거쳐 정리합니다.")
            return 0

        print("[집기] grasp_z까지 천천히 하강합니다.")
        motion["needs_lift"] = True
        arm.move_to(
            x,
            y,
            grasp_z,
            duration=DESCEND_MOVE_DURATION_SEC,
            pitch=grasp_pitch,
            roll=0.0,
            refine=0,
        )
        print("[집기] 그리퍼를 닫습니다.")
        motion["holding"] = True
        arm.close_gripper()
        time.sleep(GRIPPER_CLOSE_WAIT_SEC)

        print("[집기] approach_z까지 천천히 상승합니다.")
        arm.move_to(
            x,
            y,
            approach_z,
            duration=DESCEND_MOVE_DURATION_SEC,
            pitch=grasp_pitch,
            roll=0.0,
            refine=0,
        )
        motion["needs_lift"] = False
        print(f"[집기] 잡은 상태로 {HOLD_AFTER_LIFT_SEC:.0f}초 유지합니다.")
        time.sleep(HOLD_AFTER_LIFT_SEC)
        print("[집기] 안전 높이에서 그리퍼를 열어 호박을 내려놓습니다.")
        arm.open_gripper()
        motion["holding"] = False
        return 0

    except KeyboardInterrupt:
        print("\n사용자가 Ctrl+C로 중단했습니다.")
        return 130
    except ValueError as exc:
        print(f"이동/역기구학/관절 한계 오류: {exc}", file=sys.stderr)
        print("다른 자세로 실제 이동을 재시도하지 않고 정리합니다.")
        return 1
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        if arm is not None and motion["connected"]:
            cleanup_arm(arm, settings, motion)
        elif arm is not None:
            try:
                arm.disconnect()
            except Exception as exc:
                print(
                    f"[정리 오류] 연결 실패 후 disconnect() 실패: {exc}",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    raise SystemExit(main())
