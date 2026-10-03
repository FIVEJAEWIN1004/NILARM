"""Find the OMX arm camera (Innomaker) by V4L2 name, not by /dev/videoN number.

/dev/videoN numbers change after reboot or USB reconnect, and one physical
camera exposes several nodes (only one of them captures).  Each candidate
node must advertise YUYV 640x480 @ 30 fps.  There is no fallback to any
other camera: if no Innomaker node qualifies, harvest must not start.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


CAMERA_EXPECTED_NAME = "Innomaker-U20CAM-720P"
CAMERA_FOURCC = "YUYV"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30.0

SYSFS_V4L_DIR = Path("/sys/class/video4linux")

_FORMAT_RE = re.compile(r"\[\d+\]:\s*'(\w+)'")
_SIZE_RE = re.compile(r"Size:\s*Discrete\s+(\d+)x(\d+)")
_FPS_RE = re.compile(r"Interval:\s*Discrete\s+[\d.]+s\s*\(([\d.]+)\s*fps\)")


def supported_modes(list_formats_ext: str) -> set[tuple[str, int, int, float]]:
    """Parse `v4l2-ctl --list-formats-ext` output into (fourcc, w, h, fps)."""
    modes = set()
    fourcc = size = None
    for line in list_formats_ext.splitlines():
        if match := _FORMAT_RE.search(line):
            fourcc, size = match.group(1), None
        elif match := _SIZE_RE.search(line):
            size = (int(match.group(1)), int(match.group(2)))
        elif (match := _FPS_RE.search(line)) and fourcc and size:
            modes.add((fourcc, *size, float(match.group(1))))
    return modes


def supports_required_mode(list_formats_ext: str) -> bool:
    return any(
        fourcc == CAMERA_FOURCC
        and (width, height) == (CAMERA_WIDTH, CAMERA_HEIGHT)
        and abs(fps - CAMERA_FPS) < 0.5
        for fourcc, width, height, fps in supported_modes(list_formats_ext)
    )


def _list_formats_ext(device: str) -> str:
    try:
        result = subprocess.run(
            ["v4l2-ctl", "-d", device, "--list-formats-ext"],
            capture_output=True, text=True, timeout=5.0, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(
            f"v4l2-ctl로 {device} 형식을 확인하지 못했습니다: {error}\n"
            "sudo apt install v4l-utils 후 다시 실행하세요."
        ) from error
    return result.stdout


def _node_number(path: Path) -> int:
    return int(path.name[len("video"):])


def find_arm_camera(
    sysfs_dir: Path = SYSFS_V4L_DIR,
    list_formats_ext=_list_formats_ext,
) -> tuple[str, str]:
    """Return (device_path, device_name) of the capture-capable arm camera."""
    nodes = sorted(
        (p for p in sysfs_dir.glob("video*") if p.name[5:].isdigit()),
        key=_node_number,
    )
    seen = []
    for node in nodes:
        try:
            name = (node / "name").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        seen.append(f"/dev/{node.name} ({name})")
        if CAMERA_EXPECTED_NAME.lower() not in name.lower():
            continue
        device = f"/dev/{node.name}"
        if supports_required_mode(list_formats_ext(device)):
            return device, name

    found = "\n".join(f"- {entry}" for entry in seen) or "- (V4L2 장치 없음)"
    raise RuntimeError(
        f"{CAMERA_EXPECTED_NAME} 팔 카메라에서 {CAMERA_FOURCC} "
        f"{CAMERA_WIDTH}x{CAMERA_HEIGHT} {CAMERA_FPS:.0f}fps capture node를 "
        f"찾지 못했습니다.\n발견된 장치:\n{found}\n"
        "다른 카메라로는 실행하지 않습니다."
    )
