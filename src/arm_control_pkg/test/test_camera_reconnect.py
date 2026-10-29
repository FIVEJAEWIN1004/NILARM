"""Camera reconnect tests without opening hardware."""

from types import SimpleNamespace

import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_auto_scan_count_orange_harvest as scan,
)


class FakeCapture:
    def __init__(self, frames):
        self.frames = list(frames)
        self.released = False

    def read(self):
        if not self.frames:
            return False, None
        return self.frames.pop(0)

    def release(self):
        self.released = True


def test_reopen_releases_dead_node_and_returns_new_capture(monkeypatch):
    dead = FakeCapture([])
    recovered = FakeCapture([])
    monkeypatch.setattr(scan.base, "open_camera", lambda: recovered)

    assert scan.reopen_arm_camera(dead, 1) is recovered
    assert dead.released


def test_observe_angle_restarts_on_reconnected_camera(monkeypatch):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dead = FakeCapture([(False, None)] * (scan.SCAN_FLUSH_FRAMES + 1))
    recovered = FakeCapture(
        [(True, frame)] * (scan.SCAN_FLUSH_FRAMES + scan.SCAN_FRAME_COUNT)
    )
    monkeypatch.setattr(scan.base, "open_camera", lambda: recovered)
    monkeypatch.setattr(scan, "detect_frame", lambda *_args: (frame.copy(), []))
    monkeypatch.setattr(scan.cv2, "imshow", lambda *_args: None)
    monkeypatch.setattr(scan.cv2, "waitKey", lambda _delay: -1)

    tracks, active = scan.observe_angle(
        SimpleNamespace(),
        dead,
        {},
        {},
        -140.0,
        -139.5,
    )

    assert tracks == []
    assert active is recovered
    assert dead.released


def test_reopen_failure_is_bounded(monkeypatch):
    dead = FakeCapture([])
    monkeypatch.setattr(scan, "CAMERA_REOPEN_ATTEMPTS", 2)
    monkeypatch.setattr(scan, "CAMERA_REOPEN_DELAY_SEC", 0.0)

    def fail_open():
        raise RuntimeError("not connected")

    monkeypatch.setattr(scan.base, "open_camera", fail_open)

    with pytest.raises(RuntimeError, match="새 capture 장치를 열지 못했습니다"):
        scan.reopen_arm_camera(dead, 1)
    assert dead.released
