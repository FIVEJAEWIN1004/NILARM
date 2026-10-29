"""Mocked tests for the applied arm-camera capture settings."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from arm_control_pkg.pumpkin_harvest import (
    pumpkin_detected_approach_validation as camera_module,
)


class FakeCapture:
    def __init__(
        self,
        fourcc="MJPG",
        frame_shape=(480, 640, 3),
        fps=26.5,
        read_ok=True,
    ):
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc)
        self.frame_shape = frame_shape
        self.fps = fps
        self.read_ok = read_ok
        self.released = False
        self.settings = []

    def set(self, property_id, value):
        self.settings.append((property_id, value))
        return True

    def get(self, property_id):
        values = {
            cv2.CAP_PROP_FOURCC: self.fourcc,
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: self.fps,
        }
        return values.get(property_id, 0)

    def isOpened(self):
        return True

    def read(self):
        if not self.read_ok:
            return False, None
        return True, np.zeros(self.frame_shape, dtype=np.uint8)

    def release(self):
        self.released = True


def install_fake_capture(monkeypatch, capture):
    monkeypatch.setattr(
        camera_module, "verified_camera_source", lambda: "/dev/video-test"
    )
    monkeypatch.setattr(
        camera_module.cv2, "VideoCapture", lambda _source, _backend: capture
    )


def test_accepts_mjpg_640x480_and_reported_26_5_fps(monkeypatch, capsys):
    capture = FakeCapture(fps=26.5)
    install_fake_capture(monkeypatch, capture)

    assert camera_module.open_camera() is capture
    assert not capture.released
    assert "FOURCC=MJPG, 640x480, FPS=26.5" in capsys.readouterr().out
    assert (cv2.CAP_PROP_FPS, camera_module.CAMERA_FPS) in capture.settings


def test_rejects_applied_yuyv_and_releases_camera(monkeypatch):
    capture = FakeCapture(fourcc="YUYV")
    install_fake_capture(monkeypatch, capture)

    with pytest.raises(RuntimeError, match="필요한 형식은 MJPG"):
        camera_module.open_camera()
    assert capture.released


def test_rejects_wrong_frame_size_and_releases_camera(monkeypatch):
    capture = FakeCapture(frame_shape=(720, 1280, 3))
    install_fake_capture(monkeypatch, capture)

    with pytest.raises(RuntimeError, match="영상 크기가 1280x720"):
        camera_module.open_camera()
    assert capture.released


def test_rejects_missing_frames_and_releases_camera(monkeypatch):
    capture = FakeCapture(read_ok=False)
    install_fake_capture(monkeypatch, capture)

    with pytest.raises(RuntimeError, match="warm-up"):
        camera_module.open_camera()
    assert capture.released
