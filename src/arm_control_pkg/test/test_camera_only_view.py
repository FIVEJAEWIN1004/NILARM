"""Safety checks for the motion-free arm-camera preview."""

from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys


PACKAGE_DIR = Path(__file__).resolve().parents[1] / "arm_control_pkg"
TOOL_PATH = (
    PACKAGE_DIR
    / "pumpkin_harvest"
    / "tools"
    / "pumpkin_camera_only_view.py"
)


def test_camera_only_tool_has_no_hardware_control_imports_or_calls():
    source = TOOL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = set()
    called_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                called_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                called_names.add(function.attr)

    assert not any(name == "omx_f" or name.startswith("omx_f.")
                   for name in imported_modules)
    assert not any("gripper" in name.lower() for name in imported_modules)
    assert not any("rclpy" in name.lower() for name in imported_modules)
    assert {"connect", "ready", "move_joints", "park", "gripper"}.isdisjoint(
        called_names
    )


def test_camera_only_import_chain_does_not_load_omx_or_gripper_modules():
    code = """
import sys
import arm_control_pkg.pumpkin_harvest.tools.pumpkin_camera_only_view
loaded = [name for name in sys.modules
          if name == 'omx_f' or name.startswith('omx_f.')
          or 'gripper' in name.lower()]
if loaded:
    raise SystemExit('hardware modules loaded: ' + ', '.join(loaded))
"""
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        path for path in (str(PACKAGE_DIR.parent), existing_pythonpath) if path
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30.0,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr or result.stdout
