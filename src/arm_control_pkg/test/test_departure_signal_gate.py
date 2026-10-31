"""Departure gate tests (automatic by default) without robot hardware."""

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v2 as poses,
)
from arm_control_pkg.pumpkin_harvest import (
    pumpkin_full_auto_orange_harvest_to_bin_v4 as deposit,
)


class RecordingArm:
    hz = 100.0

    def __init__(self, events):
        self.events = events
        self.kin = None

    def check_limits(self, q, _current=None):
        return np.asarray(q, dtype=float)

    def _write(self, _q):
        pass

    def move_joints(self, joints, duration):
        self.events.append(("move", tuple(np.asarray(joints)), duration))

    def open_gripper(self, **_kwargs):
        self.events.append(("open",))

    def gripper(self, *_args, **_kwargs):
        self.events.append((
            "open" if _kwargs.get("stall_guard") else "restore_gripper",
        ))


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

    def park(self, duration=None):
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
        (deposit, "departure_signal_gate"), (scan, "park_arm"),
    ):  # run_harvest rewires these; restore them after the test
        monkeypatch.setattr(module, name, getattr(module, name))
    monkeypatch.setattr(scan.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        poses.joint_trajectory, "stream",
        lambda path, write, _hz: [write(point) for point in path] and 0)
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
        lambda *_args, **_kwargs: (
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


# --- ㉔ departure_ready: Pinky leaves after the last ⑲ rise + settle ---------

FOUR = [(0.10, 0.10), (0.20, 0.10), (0.10, -0.20), (0.25, -0.20)]


def run_recorded(monkeypatch, pumpkins=FOUR, cancel=lambda: False, **kwargs):
    """Real v5 run; arm events, sleeps and feedback in one ordered list."""
    events = []
    install_fake_hardware(monkeypatch, events, pumpkins)
    no_stdin(monkeypatch)
    monkeypatch.setattr(scan.time, "sleep",
                        lambda seconds: events.append(("sleep", seconds)))
    kwargs.setdefault("require_departure_confirmation", False)
    try:
        result = v5.run_harvest(
            target_count=None,
            feedback_callback=lambda count, status: events.append(
                ("fb", count, status)),
            cancel_callback=cancel,
            **kwargs,
        )
    except scan.HarvestExecutionError as error:
        result = error
    return events, result


def departures(events):
    return [i for i, e in enumerate(events) if e[:1] == ("fb",)
            and e[2] == "departure_ready"]


def test_departure_ready_once_after_last_rise_and_settle(monkeypatch):
    events, result = run_recorded(monkeypatch)
    assert result.harvested_count == 4
    (at,) = departures(events)  # exactly once, for the 4-pumpkin run
    assert events[at] == ("fb", 4, "departure_ready")
    # ⑱ release, 0.7 s drop wait, ⑲ open-gripper rise, 0.7 s settle, then ㉔.
    assert [e[0] for e in events[at - 4:at]] == ["open", "sleep", "move", "sleep"]
    assert events[at - 3][1] == events[at - 1][1] == deposit.BIN_SETTLE_SEC
    # Pumpkins 1-3 were all released before, without any departure_ready.
    assert [e[0] for e in events[:at]].count("open") == 4
    # ㉑ gripper restore / fold / centre return and ㉒ park still run after.
    after = [e[0] for e in events[at + 1:]]
    assert after == ["restore_gripper", "move", "move", "sleep", "fb", "fb", "park"]
    assert ("fb", 4, "completed") in events[at + 1:]
    assert events.index(("fb", 4, "placing")) > at  # counted after ⑲


def test_single_pumpkin_is_also_last(monkeypatch):
    events, _ = run_recorded(monkeypatch, pumpkins=[(0.10, 0.10)])
    assert [events[i] for i in departures(events)] == [("fb", 1, "departure_ready")]


def test_flag_off_keeps_result_based_departure(monkeypatch):
    monkeypatch.setattr(deposit, "ENABLE_PINKY_DEPARTURE_AFTER_LAST_RISE", False)
    events, result = run_recorded(monkeypatch)
    assert departures(events) == [] and result.harvested_count == 4
    assert ("fb", 4, "completed") in events


def test_missed_pumpkin_never_signals_departure(monkeypatch):
    # 2nd pumpkin's IK fails: 3 of 4 harvested, the "last" index is never hit.
    events = []
    install_fake_hardware(monkeypatch, events, FOUR)
    no_stdin(monkeypatch)
    fake_plan = scan.multi.plan_fixed_pose_stages_from_folded_pose
    calls = []

    def plan(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise ValueError("unreachable")
        return fake_plan(*args, **kwargs)

    monkeypatch.setattr(scan.multi, "plan_fixed_pose_stages_from_folded_pose", plan)
    feedback = []
    result = v5.run_harvest(
        feedback_callback=lambda c, s: feedback.append((c, s)))
    assert result.harvested_count == 3 and result.attempted_count == 4
    assert not any(s == "departure_ready" for _c, s in feedback)
    assert feedback[-1] == (3, "failed")


@pytest.mark.parametrize("fail_at", ["release", "rise", "settle"])
def test_failure_before_departure_point_never_signals(monkeypatch, fail_at):
    original_gripper = FakeOmx.gripper
    original_move = FakeOmx.move_joints
    hits = {"open": 0}

    def gripper(self, *args, **kwargs):
        if kwargs.get("stall_guard"):
            hits["open"] += 1
            if fail_at == "release" and hits["open"] == 4:
                raise RuntimeError("gripper comm error")
        return original_gripper(self, *args, **kwargs)

    def move_joints(self, joints, duration):
        # After the 4th release the next move is the ⑲ rise.
        if fail_at == "rise" and hits["open"] == 4 and self.events[-1][0] == "sleep":
            raise RuntimeError("joint limit")
        return original_move(self, joints, duration)

    monkeypatch.setattr(FakeOmx, "gripper", gripper)
    monkeypatch.setattr(FakeOmx, "move_joints", move_joints)
    if fail_at == "settle":
        real_settle = deposit.settle_after_arm_move

        def settle(arm, target, seconds, *rest):
            if hits["open"] == 4:
                raise RuntimeError("settle feedback lost")
            return real_settle(arm, target, seconds, *rest)
        monkeypatch.setattr(deposit, "settle_after_arm_move", settle)
    events, result = run_recorded(monkeypatch)
    assert isinstance(result, scan.HarvestExecutionError)
    assert result.harvested_count == 3
    assert departures(events) == []
    assert ("fb", 3, "failed") in events


def test_cancel_requested_before_gate_never_signals(monkeypatch):
    seen = {"open": 0}

    def cancel():
        return seen["open"] >= 4

    original = FakeOmx.gripper

    def gripper(self, *args, **kwargs):
        if kwargs.get("stall_guard"):
            seen["open"] += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(FakeOmx, "gripper", gripper)
    events, result = run_recorded(monkeypatch, cancel=cancel)
    assert departures(events) == []
    assert result.cancelled


def test_manual_gate_signals_once_after_enter(monkeypatch):
    events = []
    install_fake_hardware(monkeypatch, events, FOUR)
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))
    feedback = []
    result = v5.run_harvest(
        require_departure_confirmation=True,
        feedback_callback=lambda c, s: feedback.append((c, s)))
    assert result.harvested_count == 4
    assert [f for f in feedback if f[1] == "departure_ready"] == [(4, "departure_ready")]


def test_server_forwards_departure_ready_as_action_feedback(monkeypatch):
    """The real Action server sends it as Feedback(status=departure_ready)."""
    class GoalHandle:
        is_cancel_requested = False

        def __init__(self):
            self.request = server.Harvest.Goal(target_count=1)
            self.feedback = []
            self.state = None

        def publish_feedback(self, message):
            self.feedback.append((message.current_count, message.status))

        def succeed(self):
            self.state = "succeeded"

        def abort(self):
            self.state = "aborted"

    def fake_run(**kwargs):
        kwargs["feedback_callback"](2, "departure_ready")
        kwargs["feedback_callback"](2, "completed")
        return scan.HarvestRunResult(2, 2, 2)

    import rclpy
    rclpy.init()
    try:
        node = server.HarvestActionServer()
        node.set_parameters([rclpy.parameter.Parameter(
            "harvest_all_detected", value=True)])
        monkeypatch.setattr(node._prescan, "harvest", fake_run)
        handle = GoalHandle()
        result = node._execute_callback(handle)
        node.destroy_node()
    finally:
        rclpy.shutdown()
    assert handle.feedback == [(2, "departure_ready"), (2, "completed")]
    assert handle.state == "succeeded" and result.success  # result unchanged
