"""Measure residual XY error between YOLO prediction and the real pumpkin.

This is a calibration-only program.  It never descends automatically, closes
the gripper, or harvests a pumpkin.  Place exactly one pumpkin in the selected
camera view.  After detection, teach the arm by hand so that the centre between
the gripper fingers is directly above the real pumpkin centre, then press
Enter.  The program stores predicted/actual XY pairs and fits a correction.
"""

import json
import math
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from omx_f import OmxFollower
from pumpkin_scan_count import (
    CALIBRATION_PATH,
    JOINT1_SAFE_LIMIT_DEG,
    MODEL_PATH,
    MOVE_DURATION_SEC,
    SETTLE_TIME_SEC,
    load_calibration,
    observe_view,
    open_camera,
    valid_clusters,
    validate_model,
)


OUTPUT_PATH = Path(__file__).with_name("pumpkin_grasp_xy_correction.json")
RETURN_DURATION_SEC = 10.0
ALLOWED_OFFSETS_DEG = (-140, -110, -80, -50, -20, 0, 10, 40, 70, 100, 130, 140)


def load_samples():
    if not OUTPUT_PATH.is_file():
        return []

    data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    if not isinstance(samples, list):
        raise ValueError(f"{OUTPUT_PATH.name}의 samples 형식이 올바르지 않습니다.")
    return samples


def fit_correction(samples):
    """Return an XY correction model using all saved calibration samples."""
    predicted = np.asarray([sample["predicted_xy_m"] for sample in samples], dtype=float)
    actual = np.asarray([sample["actual_xy_m"] for sample in samples], dtype=float)

    errors = actual - predicted
    mean_error = np.mean(errors, axis=0)

    result = {
        "sample_count": len(samples),
        "mean_error_m": mean_error.tolist(),
        "mean_error_mm": (mean_error * 1000.0).tolist(),
    }

    # Three non-collinear points are the minimum for a 2-D affine fit.
    design = np.column_stack((predicted, np.ones(len(predicted))))
    if len(samples) >= 3 and np.linalg.matrix_rank(design) == 3:
        coefficients, _, _, _ = np.linalg.lstsq(design, actual, rcond=None)
        matrix = coefficients[:2, :].T
        bias = coefficients[2, :]
        corrected = predicted @ matrix.T + bias
        residual = actual - corrected

        result.update(
            {
                "type": "affine",
                "matrix": matrix.tolist(),
                "bias_m": bias.tolist(),
                "rms_residual_mm": float(
                    np.sqrt(np.mean(np.sum(residual**2, axis=1))) * 1000.0
                ),
                "max_residual_mm": float(
                    np.max(np.linalg.norm(residual, axis=1)) * 1000.0
                ),
            }
        )
    else:
        result.update(
            {
                "type": "translation",
                "dx_m": float(mean_error[0]),
                "dy_m": float(mean_error[1]),
                "note": "3개 이상의 서로 다른 위치가 모이면 affine 보정으로 갱신됩니다.",
            }
        )

    return result


def save_sample(sample):
    samples = load_samples()
    samples.append(sample)
    correction = fit_correction(samples)

    payload = {
        "format_version": 1,
        "calibration_source": str(CALIBRATION_PATH),
        "instructions": (
            "corrected_xy = matrix @ predicted_xy + bias_m when type=affine; "
            "otherwise add dx_m and dy_m"
        ),
        "samples": samples,
        "correction": correction,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return correction


def ask_offset():
    allowed_text = ", ".join(f"{value:+d}" for value in ALLOWED_OFFSETS_DEG)
    while True:
        value = input(
            "\n호박이 보이는 촬영 offset 각도를 입력하세요\n"
            f"사용 가능: {allowed_text}\n"
            "offset [deg] (종료 Q): "
        ).strip()
        if value.upper() == "Q":
            return None
        try:
            offset = int(value)
        except ValueError:
            print("정수 각도를 입력하세요.")
            continue
        if offset not in ALLOWED_OFFSETS_DEG:
            print("목록에 있는 각도를 입력하세요.")
            continue
        return float(offset)


def detect_exactly_one(model, cap, calibration, offset_deg):
    clusters = []
    display_state = {"show_total": True}
    count, stop_requested = observe_view(
        model,
        cap,
        calibration,
        offset_deg,
        0,
        clusters,
        display_state,
    )
    cv2.destroyAllWindows()

    if stop_requested:
        return None

    targets = list(valid_clusters(clusters))
    if count != 1 or len(targets) != 1:
        print(
            f"[취소] 화면 검출={count}개, 유효 좌표={len(targets)}개입니다. "
            "호박을 정확히 하나만 보이게 한 뒤 다시 시도하세요."
        )
        return None
    return targets[0]


def main():
    arm = None
    cap = None
    calibration = None
    normal_finish = False

    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"YOLO 모델이 없습니다: {MODEL_PATH}")

        calibration = load_calibration()
        model = YOLO(str(MODEL_PATH))
        validate_model(model)
        cap = open_camera(calibration)

        print("OMX 로봇팔에 연결합니다.")
        arm = OmxFollower().connect()
        arm.ready(duration=5.0)

        camera_joints = np.asarray(calibration["camera_joints"], dtype=float)
        base_joint1_deg = float(np.degrees(camera_joints[0]))

        print("저장된 중앙 카메라 자세로 이동합니다.")
        arm.move_joints(camera_joints, duration=MOVE_DURATION_SEC)
        time.sleep(SETTLE_TIME_SEC)

        print("\n이 프로그램은 자동 집기, 자동 하강, 그리퍼 닫기를 하지 않습니다.")
        print("화면에는 보정용 호박을 딱 하나만 놓으세요.")

        while True:
            offset_deg = ask_offset()
            if offset_deg is None:
                break

            target_joint1_deg = base_joint1_deg + offset_deg
            if abs(target_joint1_deg) > JOINT1_SAFE_LIMIT_DEG:
                print(
                    f"[취소] joint1={target_joint1_deg:.1f}도가 "
                    "설정된 안전 범위를 벗어납니다."
                )
                continue

            target_joints = camera_joints.copy()
            target_joints[0] = np.radians(target_joint1_deg)
            print(
                f"[촬영] offset={offset_deg:+.0f}도, "
                f"joint1={target_joint1_deg:.1f}도로 이동합니다."
            )
            arm.move_joints(target_joints, duration=MOVE_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            target = detect_exactly_one(
                model,
                cap,
                calibration,
                offset_deg,
            )
            if target is None:
                continue

            predicted_xy = np.asarray([target.x, target.y], dtype=float)
            print(
                "[YOLO 예측] "
                f"x={predicted_xy[0]:.4f} m, "
                f"y={predicted_xy[1]:.4f} m, "
                f"confidence={target.confidence:.2f}"
            )

            print("teach 전에 중앙 카메라 자세로 천천히 돌아갑니다.")
            arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            confirm = input(
                "팔을 두 손으로 받칠 준비가 되면 TEACH를 입력하세요 "
                "(이번 표본 취소는 Enter): "
            ).strip()
            if confirm != "TEACH":
                print("이번 표본을 취소했습니다.")
                continue

            print("\nteach 모드입니다. 모터 힘이 빠지므로 팔을 계속 받치세요.")
            print("그리퍼 두 손가락 사이의 중심을 실제 호박 중심 바로 위에 맞추세요.")
            print("바닥까지 내리거나 그리퍼를 닫을 필요는 없습니다.")
            with arm.teach():
                input("정확히 맞춘 상태에서, 팔을 받친 채 Enter: ")
                actual_pose = np.asarray(arm.pose(), dtype=float)

            if actual_pose.shape[0] < 3 or not np.all(np.isfinite(actual_pose[:3])):
                raise ValueError("teach에서 읽은 팔 끝 좌표가 올바르지 않습니다.")

            actual_xy = actual_pose[:2]
            error_xy = actual_xy - predicted_xy
            error_norm_mm = float(np.linalg.norm(error_xy) * 1000.0)
            zone = "A" if float(predicted_xy[1]) >= 0.0 else "B"

            sample = {
                "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                "zone": zone,
                "view_offset_deg": offset_deg,
                "confidence": float(target.confidence),
                "predicted_xy_m": predicted_xy.tolist(),
                "actual_xy_m": actual_xy.tolist(),
                "teach_pose_m": actual_pose[:3].tolist(),
                "error_xy_m": error_xy.tolist(),
                "error_xy_mm": (error_xy * 1000.0).tolist(),
                "error_norm_mm": error_norm_mm,
            }
            correction = save_sample(sample)

            print(
                "\n[저장 완료] "
                f"dx={error_xy[0] * 1000.0:+.1f} mm, "
                f"dy={error_xy[1] * 1000.0:+.1f} mm, "
                f"전체 오차={error_norm_mm:.1f} mm"
            )
            print(f"누적 표본: {correction['sample_count']}개")
            print(f"저장 파일: {OUTPUT_PATH}")

            print("다음 촬영을 위해 중앙 카메라 자세로 천천히 이동합니다.")
            arm.move_joints(camera_joints, duration=RETURN_DURATION_SEC)
            time.sleep(SETTLE_TIME_SEC)

            again = input("다른 위치도 계속 보정하려면 Enter, 종료는 Q: ").strip()
            if again.upper() == "Q":
                break

        normal_finish = True

    except KeyboardInterrupt:
        print("\n사용자가 보정을 중단했습니다.")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        if arm is not None:
            try:
                if normal_finish and calibration is not None:
                    print("중앙 카메라 자세로 돌아갑니다.")
                    arm.move_joints(
                        np.asarray(calibration["camera_joints"], dtype=float),
                        duration=RETURN_DURATION_SEC,
                    )
                    print("정리 자세로 이동합니다.")
                    arm.park()
                else:
                    print(
                        "비정상 종료되어 자동 복귀 동작을 생략합니다. "
                        "팔을 받친 상태에서 로봇 상태를 확인하세요."
                    )
            finally:
                try:
                    arm.disconnect()
                except Exception as error:
                    print(f"연결 종료 중 오류: {error}")


if __name__ == "__main__":
    main()
