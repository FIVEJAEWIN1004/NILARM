"""Departure gate tests (automatic by default) without robot hardware."""

import numpy as np

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as poses,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as deposit,
)


class RecordingArm:
    def __init__(self, events):
        self.events = events
        self.kin = None

    def move_joints(self, joints, duration):
        self.events.append(("move", tuple(np.asarray(joints)), duration))

    def open_gripper(self, **_kwargs):
        self.events.append(("open",))

    def gripper(self, *_args, **_kwargs):
        self.events.append(("restore_gripper",))


def install_poses(monkeypatch):
    monkeypatch.setattr(poses, "_BIN_HOVER_JOINTS", np.full(5, 1.0))
    monkeypatch.setattr(poses, "_BIN_DROP_JOINTS", np.full(5, 2.0))
    monkeypatch.setattr(poses, "_BIN_FOLDED_JOINTS", np.full(5, 3.0))
    monkeypatch.setattr(deposit.time, "sleep", lambda _seconds: None)


def test_last_pumpkin_gate_is_after_hover_rise_before_arm_cleanup(monkeypatch):
    events = []
    install_poses(monkeypatch)
    monkeypatch.setattr(
        deposit,
        "departure_signal_gate",
        lambda: events.append(("departure_gate",)),
    )
    arm = RecordingArm(events)
    calibration = {"camera_joints": np.zeros(5)}

    deposit.deposit_open_then_rise(
        arm,
        calibration,
        default_gripper_value=0.3,
        is_last=True,
    )

    names = [event[0] for event in events]
    assert names[:5] == ["move", "move", "open", "move", "departure_gate"]
    assert names[5] == "restore_gripper"


def test_non_last_pumpkin_does_not_wait_for_departure(monkeypatch):
    events = []
    install_poses(monkeypatch)
    monkeypatch.setattr(
        deposit,
        "departure_signal_gate",
        lambda: events.append(("departure_gate",)),
    )
    arm = RecordingArm(events)

    deposit.deposit_open_then_rise(
        arm,
        {"camera_joints": np.zeros(5)},
        default_gripper_value=0.3,
        is_last=False,
    )

    assert "departure_gate" not in [event[0] for event in events]


# --- Non-interactive (server) runs: stdin has no terminal, input() -> EOF ---

import io  # noqa: E402
import sys  # noqa: E402

from arm_control_pkg.pumpkin_harvest import (  # noqa: E402
    harvest_action_server as server,
)
from arm_control_pkg.pumpkin_harvest import (  # noqa: E402
    pumpkin_full_auto_orange_harvest_to_bin_v5 as v5,
)

scan = poses.scan


def no_stdin(monkeypatch):
    # Same as the SSH/background server: any input() raises EOFError.
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))


def test_default_gate_never_reads_stdin(monkeypatch):
    events = []
    install_poses(monkeypatch)
    no_stdin(monkeypatch)
    assert deposit.departure_signal_gate is (
        deposit.continue_without_departure_signal)

    deposit.deposit_open_then_rise(
        RecordingArm(events),
        {"camera_joints": np.zeros(5)},
        default_gripper_value=0.3,
        is_last=True,
    )

    names = [event[0] for event in events]
    assert names == [
        "move", "move", "open", "move", "restore_gripper", "move", "move"]


class FakeOmx(RecordingArm):
    """Whole OMX surface used by scan.main / harvest_one_direct."""

    def connect(self):
        return self

    def ready(self, **_kwargs):
        pass

    def joints(self):
        return np.zeros(5)

    def close_gripper(self, **_kwargs):
        self.events.append(("close",))

    def park(self):
        self.events.append(("park",))

    def disconnect(self):
        pass


def fake_track(x, y):
    detection = scan.Detection(
        target={"world_target_xy": [x, y], "planned_grasp_z": 0.02},
        label="ORANGE",
        orange_ratio=0.9,
        green_ratio=0.0,
        confidence=0.9,
        image_margin_px=50.0,
        commanded_offset_deg=-140.0,
        measured_offset_deg=-140.0,
    )
    return scan.ViewTrack(x=x, y=y, detections=[detection])


def install_fake_hardware(monkeypatch, events, pumpkins):
    """Real v5/scan/v2/v4 logic; only camera, YOLO, IK and OMX are fake."""
    zeros = np.zeros(5)
    monkeypatch.setattr(v5, "_SPEED_CONFIGURED", True)  # keep real speeds
    for module, name in (
        (scan, "require_start"), (scan, "add_global_track"),
        (scan, "print_summary"), (scan, "harvest_one"),
        (scan, "AUTO_COUNTDOWN_SEC"), (poses, "DROP_RAISE_M"),
        (poses, "deposit_and_prepare_next"), (poses, "_BIN_HOVER_JOINTS"),
        (poses, "_BIN_DROP_JOINTS"), (poses, "_BIN_FOLDED_JOINTS"),
        (deposit, "departure_signal_gate"),
    ):  # run_harvest rewires these; restore them after the test
        monkeypatch.setattr(module, name, getattr(module, name))
    monkeypatch.setattr(scan.time, "sleep", lambda _s: None)
    monkeypatch.setattr(scan.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(scan.base, "load_calibrations", lambda: {
        "camera_joints": zeros, "pitch_rad": 0.0, "roll_rad": 0.0})
    monkeypatch.setattr(scan.multi, "load_angle_residuals", lambda: {
        angle: (0.0, 0.0) for angle in scan.SCAN_OFFSETS_DEG})
    monkeypatch.setattr(scan.base, "find_model_path", lambda: "fake.pt")
    monkeypatch.setattr(scan, "YOLO", lambda _path: object())
    monkeypatch.setattr(scan.base, "validate_model", lambda _model: None)

    class FakeCap:
        def release(self):
            pass

    monkeypatch.setattr(scan.base, "open_camera", FakeCap)
    monkeypatch.setattr(scan, "OmxFollower", lambda: FakeOmx(events))
    monkeypatch.setattr(scan, "normalized_gripper_value", lambda _arm: 0.3)

    def observe(_model, cap, *_args):
        first_view = _args[-2] == -140.0
        tracks = [fake_track(x, y) for x, y in pumpkins] if first_view else []
        return tracks, cap

    monkeypatch.setattr(scan, "observe_angle", observe)
    monkeypatch.setattr(
        scan.multi, "plan_fixed_pose_stages_from_folded_pose",
        lambda *_args: (
            zeros, 10.0, [np.full(5, i, dtype=float) for i in range(4)], None),
    )


def test_server_flow_counts_last_pumpkin_and_succeeds_without_stdin(
        monkeypatch):
    events = []
    feedback = []
    pumpkins = [(0.10, 0.10), (0.20, 0.10), (0.10, -0.20), (0.25, -0.20)]
    install_fake_hardware(monkeypatch, events, pumpkins)
    no_stdin(monkeypatch)

    # Exactly the arguments harvest_action_server passes with
    # harvest_all_detected=true (target_count=None).
    result = v5.run_harvest(
        target_count=None,
        require_start_confirmation=False,
        require_harvest_confirmation=False,
        require_departure_confirmation=False,
        feedback_callback=lambda count, status: feedback.append(
            (count, status)),
        cancel_callback=lambda: False,
    )

    assert result.detected_ripe_count == 4
    assert result.attempted_count == 4
    assert result.harvested_count == 4  # the last pumpkin is counted
    assert not result.cancelled
    assert (4, "placing") in feedback
    assert feedback[-1] == (4, "completed")
    assert [event[0] for event in events].count("open") == 4
    assert server._is_harvest_success(
        True, 1, result.detected_ripe_count, result.attempted_count,
        result.harvested_count)


def test_manual_departure_gate_is_opt_in_only(monkeypatch):
    install_fake_hardware(monkeypatch, [], [(0.10, 0.10)])
    no_stdin(monkeypatch)

    # Explicit debug option keeps the old Enter gate; with no terminal it
    # still fails exactly like the original bug, proving the default is off.
    try:
        v5.run_harvest(require_departure_confirmation=True)
    except scan.HarvestExecutionError as error:
        assert "EOF" in str(error)
        assert error.harvested_count == 0
    else:
        raise AssertionError("manual gate did not read stdin")
