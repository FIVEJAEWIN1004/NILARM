"""Arm camera discovery without opening real hardware."""

import pytest

from arm_control_pkg.pumpkin_harvest.arm_camera import find_arm_camera

INNOMAKER = "Innomaker-U20CAM-720P  : Innoma"
LAPTOP = "720p HD Camera: 720p HD Camera"

GOOD = """ioctl: VIDIOC_ENUM_FMT
\tType: Video Capture

\t[0]: 'MJPG' (Motion-JPEG, compressed)
\t\tSize: Discrete 640x480
\t\t\tInterval: Discrete 0.033s (30.000 fps)
\t[1]: 'YUYV' (YUYV 4:2:2)
\t\tSize: Discrete 1280x720
\t\t\tInterval: Discrete 0.100s (10.000 fps)
\t\tSize: Discrete 640x480
\t\t\tInterval: Discrete 0.033s (30.000 fps)
"""
METADATA_NODE = "ioctl: VIDIOC_ENUM_FMT\n\tType: Video Capture\n"
MJPG_ONLY_640 = GOOD.replace("'YUYV'", "'NV12'")
YUYV_640_SLOW = GOOD.replace(
    "Discrete 640x480\n\t\t\tInterval: Discrete 0.033s (30.000 fps)\n",
    "Discrete 640x480\n\t\t\tInterval: Discrete 0.100s (10.000 fps)\n",
).replace("'MJPG'", "'XXXX'")


def make_sysfs(tmp_path, names):
    for node, name in names.items():
        (tmp_path / node).mkdir()
        (tmp_path / node / "name").write_text(name + "\n")
    return tmp_path


def run(tmp_path, names, formats):
    return find_arm_camera(make_sysfs(tmp_path, names), formats.__getitem__)


def test_picks_innomaker_capture_node_not_laptop(tmp_path):
    names = {"video0": INNOMAKER, "video1": INNOMAKER,
             "video2": LAPTOP, "video3": LAPTOP}
    formats = {"/dev/video0": GOOD, "/dev/video1": METADATA_NODE,
               "/dev/video2": GOOD, "/dev/video3": METADATA_NODE}
    assert run(tmp_path, names, formats) == ("/dev/video0", INNOMAKER)


def test_follows_renumbering_and_skips_non_capture_node(tmp_path):
    # Laptop first, Innomaker metadata node numbered before its capture node.
    names = {"video0": LAPTOP, "video1": LAPTOP,
             "video4": INNOMAKER, "video10": INNOMAKER}
    formats = {"/dev/video0": GOOD, "/dev/video1": METADATA_NODE,
               "/dev/video4": METADATA_NODE, "/dev/video10": GOOD}
    assert run(tmp_path, names, formats) == ("/dev/video10", INNOMAKER)


@pytest.mark.parametrize("innomaker_formats", [
    METADATA_NODE, MJPG_ONLY_640, YUYV_640_SLOW])
def test_no_fallback_when_innomaker_mode_missing(tmp_path, innomaker_formats):
    names = {"video0": INNOMAKER, "video2": LAPTOP}
    formats = {"/dev/video0": innomaker_formats, "/dev/video2": GOOD}
    with pytest.raises(RuntimeError, match="다른 카메라로는 실행하지 않습니다"):
        run(tmp_path, names, formats)


def test_no_innomaker_connected(tmp_path):
    names = {"video2": LAPTOP, "video3": LAPTOP}
    formats = {"/dev/video2": GOOD, "/dev/video3": METADATA_NODE}
    with pytest.raises(RuntimeError, match="/dev/video2 \\(720p HD Camera"):
        run(tmp_path, names, formats)
