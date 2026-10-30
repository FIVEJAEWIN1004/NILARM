"""OMX pre-scan while Pinky drives: synchronization, fallback, no re-scan."""

import io
import sys
import threading
import time
from types import SimpleNamespace

from arm_control_pkg.pumpkin_harvest import (
    harvest_action_server as server,
)
from arm_control_pkg.pumpkin_harvest.prescan import PrescanCoordinator


TIMEOUT = 5.0


class FakeRun:
    """Mimics scan.main: scan -> before_harvest gate -> harvest."""

    def __init__(self, ripe=2, harvest_ok=True, fail_scans=0,
                 block_scan=False, harvest_error=None):
        self.ripe = ripe
        self.harvest_ok = harvest_ok
        self.fail_scans = fail_scans
        self.harvest_error = harvest_error
        self.scan_calls = 0
        self.gated_calls = 0
        self.harvests = 0
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()
        self.scan_started = threading.Event()
        self.release_scan = threading.Event()
        if not block_scan:
            self.release_scan.set()

    def __call__(self, target_count=None, feedback_callback=None,
                 cancel_callback=None, display_result_callback=None,
                 before_harvest=None):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.scan_calls += 1
            self.gated_calls += before_harvest is not None
            failing = self.fail_scans > 0
            self.fail_scans -= failing
        try:
            self.scan_started.set()
            assert self.release_scan.wait(TIMEOUT)
            if failing:
                raise RuntimeError('arm camera lost')
            if display_result_callback is not None:
                display_result_callback('A-1 / B-1')
            if self.ripe == 0:
                return SimpleNamespace(harvested_count=0, detected_ripe_count=0,
                                       attempted_count=0, cancelled=False)
            if before_harvest is not None and not before_harvest():
                return SimpleNamespace(
                    harvested_count=0, detected_ripe_count=self.ripe,
                    attempted_count=0, cancelled=True)
            with self.lock:
                self.harvests += 1
            if self.harvest_error is not None:
                raise self.harvest_error
            harvested = self.ripe if self.harvest_ok else self.ripe - 1
            if feedback_callback is not None:
                feedback_callback(harvested, 'completed')
            return SimpleNamespace(
                harvested_count=harvested, detected_ripe_count=self.ripe,
                attempted_count=self.ripe, cancelled=False)
        finally:
            with self.lock:
                self.active -= 1


def make(run, timeout=TIMEOUT):
    ready = threading.Event()

    def log(text):
        if 'SCAN_READY' in text:
            ready.set()

    return PrescanCoordinator(run, ready_timeout_sec=timeout, log=log), ready


def success(result):
    return server._is_harvest_success(
        True, 1, result.detected_ripe_count, result.attempted_count,
        result.harvested_count)


def test_prescan_done_first_harvests_without_rescan():
    run = FakeRun()
    coordinator, ready = make(run)
    assert coordinator.request_prescan()[0]
    assert ready.wait(TIMEOUT)
    time.sleep(0.05)
    assert run.harvests == 0  # nothing grasped before /harvest
    feedback, display = [], []

    result = coordinator.harvest(
        None, feedback_callback=lambda c, s: feedback.append((c, s)),
        display_result_callback=display.append)

    assert run.scan_calls == 1 and run.harvests == 1
    assert result.harvested_count == 2 and success(result)
    assert feedback == [(2, 'completed')]
    assert display == ['A-1 / B-1']  # A/B shown once harvest starts
    assert run.max_active == 1


def test_pinky_first_waits_for_running_scan_then_harvests():
    run = FakeRun(block_scan=True)
    coordinator, _ready = make(run)
    coordinator.request_prescan()
    assert run.scan_started.wait(TIMEOUT)
    box = {}
    goal = threading.Thread(
        target=lambda: box.setdefault('result', coordinator.harvest(None)))
    goal.start()
    time.sleep(0.1)
    assert goal.is_alive() and run.harvests == 0  # waiting, not polling

    run.release_scan.set()
    goal.join(TIMEOUT)

    assert not goal.is_alive()
    assert run.scan_calls == 1 and run.harvests == 1
    assert success(box['result']) and run.max_active == 1


def test_failed_prescan_falls_back_to_normal_scan_and_harvest():
    run = FakeRun(fail_scans=1)
    coordinator, _ready = make(run)
    coordinator.request_prescan()

    result = coordinator.harvest(1)

    assert run.scan_calls == 2 and run.gated_calls == 1
    assert run.harvests == 1 and success(result)
    assert run.max_active == 1


def test_prescan_without_ripe_pumpkins_falls_back():
    run = FakeRun(ripe=0)
    coordinator, _ready = make(run)
    coordinator.request_prescan()
    assert run.scan_started.wait(TIMEOUT)

    result = coordinator.harvest(1)

    assert run.scan_calls == 2 and run.gated_calls == 1
    assert not success(result)  # still 0 found: Pinky stays stopped


def test_consumed_prescan_is_never_reused():
    run = FakeRun()
    coordinator, ready = make(run)
    coordinator.request_prescan()
    assert ready.wait(TIMEOUT)
    coordinator.harvest(None)

    coordinator.harvest(1)  # next cycle with no new pre-scan

    assert run.scan_calls == 2 and run.gated_calls == 1
    assert run.harvests == 2


def test_stale_prescan_is_dropped_and_falls_back():
    run = FakeRun()
    coordinator, ready = make(run, timeout=0.05)
    coordinator.request_prescan()
    assert ready.wait(TIMEOUT)
    time.sleep(0.2)  # unclaimed past the ready timeout
    assert run.harvests == 0

    result = coordinator.harvest(1)

    assert run.scan_calls == 2 and run.gated_calls == 1
    assert run.harvests == 1 and success(result)
    assert run.max_active == 1


def test_new_prescan_supersedes_unclaimed_old_one():
    run = FakeRun()
    coordinator, ready = make(run)
    coordinator.request_prescan()
    assert ready.wait(TIMEOUT)
    ready.clear()
    ok, message = coordinator.request_prescan()
    assert ok and 'previous' in message
    assert ready.wait(TIMEOUT)

    coordinator.harvest(None)

    assert run.scan_calls == 2 and run.harvests == 1  # old one never harvests
    assert run.max_active == 1


def test_partial_harvest_stays_failure():
    run = FakeRun(harvest_ok=False)
    coordinator, ready = make(run)
    coordinator.request_prescan()
    assert ready.wait(TIMEOUT)

    result = coordinator.harvest(None)

    assert result.harvested_count == 1 and not success(result)


def test_harvest_error_after_prescan_reaches_the_goal():
    error = RuntimeError('gripper fault')
    run = FakeRun(harvest_error=error)
    coordinator, ready = make(run)
    coordinator.request_prescan()
    assert ready.wait(TIMEOUT)

    try:
        coordinator.harvest(None)
    except RuntimeError as raised:
        assert raised is error
    else:
        raise AssertionError('harvest error was swallowed')
    assert run.scan_calls == 1  # no silent re-scan after a real failure


def test_prescan_refused_while_harvesting():
    run = FakeRun(block_scan=True)
    coordinator, _ready = make(run)
    goal = threading.Thread(target=lambda: coordinator.harvest(1))
    goal.start()
    assert run.scan_started.wait(TIMEOUT)

    ok, _message = coordinator.request_prescan()
    run.release_scan.set()
    goal.join(TIMEOUT)

    assert not ok and run.scan_calls == 1


# --- real v5 -> scan -> v2 -> v4 code, fake OMX/camera/YOLO, no stdin ------

from test_departure_signal_gate import (  # noqa: E402
    install_fake_hardware, scan,
)


def test_real_pipeline_prescan_then_harvest_scans_once(monkeypatch):
    events = []
    pumpkins = [(0.10, 0.10), (0.20, 0.10), (0.10, -0.20), (0.25, -0.20)]
    install_fake_hardware(monkeypatch, events, pumpkins)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(''))  # background server
    views = []
    observe = scan.observe_angle
    monkeypatch.setattr(
        scan, 'observe_angle',
        lambda *args: views.append(args[4]) or observe(*args))
    run = server._run_v5_harvest
    coordinator, ready = make(lambda **kwargs: run(**kwargs))
    feedback = []

    assert coordinator.request_prescan()[0]
    assert ready.wait(TIMEOUT)
    assert 'close' not in [event[0] for event in events]  # no grasp yet
    assert len(views) == len(scan.SCAN_OFFSETS_DEG)

    result = coordinator.harvest(
        None, feedback_callback=lambda c, s: feedback.append((c, s)))

    assert len(views) == len(scan.SCAN_OFFSETS_DEG)  # never scanned twice
    assert result.harvested_count == 4 and result.detected_ripe_count == 4
    assert feedback[-1] == (4, 'completed') and success(result)
    names = [event[0] for event in events]
    assert names.count('close') == 4 and names[-1] == 'park'


def test_real_pipeline_stale_prescan_parks_then_fallback_scans(monkeypatch):
    events = []
    install_fake_hardware(monkeypatch, events, [(0.10, 0.10)])
    monkeypatch.setattr(sys, 'stdin', io.StringIO(''))
    run = server._run_v5_harvest
    coordinator, ready = make(lambda **kwargs: run(**kwargs), timeout=0.05)
    coordinator.request_prescan()
    assert ready.wait(TIMEOUT)
    deadline = time.monotonic() + TIMEOUT  # time.sleep is faked here
    while ('park',) not in events and time.monotonic() < deadline:
        threading.Event().wait(0.01)
    names = [event[0] for event in events]
    assert 'close' not in names and names[-1] == 'park'  # abandoned safely

    result = coordinator.harvest(None)

    assert result.harvested_count == 1 and success(result)


def test_server_prescan_service_rules():
    import rclpy
    from rclpy.parameter import Parameter
    from std_srvs.srv import Trigger

    rclpy.init()
    node = server.HarvestActionServer()
    try:
        calls = []
        node._prescan.request_prescan = lambda: calls.append(1) or (True, 'ok')
        refused = node._prescan_callback(Trigger.Request(), Trigger.Response())
        assert not refused.success and calls == []  # default: not all-detected

        node.set_parameters([Parameter('harvest_all_detected', value=True)])
        node._goal_active = True
        busy = node._prescan_callback(Trigger.Request(), Trigger.Response())
        assert not busy.success and calls == []

        node._goal_active = False
        started = node._prescan_callback(Trigger.Request(), Trigger.Response())
        assert started.success and calls == [1]
    finally:
        node.destroy_node()
        rclpy.shutdown()
