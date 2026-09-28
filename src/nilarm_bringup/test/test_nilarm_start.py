"""nilarm-start safety gate with a stub `ros2` (no ROS graph, no robot)."""

import os
import pathlib
import stat
import subprocess

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'nilarm-start'

STUB = r'''#!/usr/bin/env bash
echo "$*" >> "$STUB_LOG"
case "$1 $2" in
  "node list") for _ in $(seq 1 "$STUB_DRIVES"); do echo /camera_straight_drive; done ;;
  "service list") [[ "$STUB_SERVICE" == 1 ]] && echo /camera_drive/enable ;;
  "topic info")
    case "$3" in
      /camera/image/compressed) echo "Publisher count: $STUB_CAMERA" ;;
      /odom) echo "Publisher count: $STUB_ODOM" ;;
    esac ;;
  "action info") printf 'Action: /harvest\nAction clients: 1\n    /x\nAction servers: %s\n' "$STUB_HARVEST" ;;
  "service call") echo "response: std_srvs.srv.SetBool_Response(success=True, message='armed')" ;;
esac
'''

READY = {'STUB_DRIVES': '1', 'STUB_SERVICE': '1', 'STUB_CAMERA': '1',
         'STUB_ODOM': '1', 'STUB_HARVEST': '1'}


def run(tmp_path, **overrides):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir(exist_ok=True)
    stub = bin_dir / 'ros2'
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / 'calls.log'
    log.write_text('')
    env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}',
               NILARM_ENV_SCRIPT='/dev/null', NILARM_READY_TIMEOUT='0',
               STUB_LOG=str(log), **READY)
    env.update(overrides)
    result = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True,
                            text=True, timeout=30)
    enabled = any(line.startswith('service call') for line in log.read_text().splitlines())
    return result, enabled


def test_all_ready_arms_drive(tmp_path):
    result, enabled = run(tmp_path)
    assert result.returncode == 0 and enabled
    assert 'STARTED' in result.stdout


@pytest.mark.parametrize('missing', [
    {'STUB_DRIVES': '0'}, {'STUB_DRIVES': '4'}, {'STUB_SERVICE': '0'},
    {'STUB_CAMERA': '0'}, {'STUB_ODOM': '0'}, {'STUB_HARVEST': '0'}])
def test_any_missing_condition_never_enables(tmp_path, missing):
    result, enabled = run(tmp_path, **missing)
    assert result.returncode == 1 and not enabled
    assert 'NOT STARTED' in result.stderr


def test_gives_up_when_launch_is_gone(tmp_path):
    result, enabled = run(tmp_path, NILARM_LAUNCH_PID='999999999')
    assert result.returncode == 1 and not enabled
