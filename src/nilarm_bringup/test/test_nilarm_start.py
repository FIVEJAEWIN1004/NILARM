"""nilarm-start / remote harvest safety gate with stub `ros2` + `ssh`.

No ROS graph, no network, no robot: /camera_drive/enable is only ever "called"
on the stub, and the laptop server launch is replaced by a stub `setsid`.
"""

import os
import pathlib
import shutil
import stat
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'src' / 'nilarm_bringup' / 'scripts' / 'nilarm-start'
RUNNER = ROOT / 'scripts' / 'run_harvest_server.sh'

ROS2_STUB = r'''#!/usr/bin/env bash
echo "ros2 $*" >> "$STUB_LOG"
harvest="$STUB_HARVEST"
[[ -f "$STUB_STARTED" ]] && harvest=1
case "$1 $2" in
  "node list") for _ in $(seq 1 "$STUB_DRIVES"); do echo /camera_straight_drive; done ;;
  "service list") [[ "$STUB_SERVICE" == 1 ]] && echo /camera_drive/enable ;;
  "topic info")
    case "$3" in
      /camera/image/compressed) echo "Publisher count: $STUB_CAMERA" ;;
      /odom) echo "Publisher count: $STUB_ODOM" ;;
    esac ;;
  "action info") printf 'Action: /harvest\nAction clients: 1\n    /x\nAction servers: %s\n' "$harvest" ;;
  "service call") echo "response: std_srvs.srv.SetBool_Response(success=True, message='armed')" ;;
esac
'''

SSH_STUB = r'''#!/usr/bin/env bash
echo "ssh $*" >> "$STUB_LOG"
[[ "$STUB_SSH_RC" == 0 && "$STUB_SSH_STARTS_SERVER" == 1 ]] && touch "$STUB_STARTED"
exit "$STUB_SSH_RC"
'''

READY = {'STUB_DRIVES': '1', 'STUB_SERVICE': '1', 'STUB_CAMERA': '1',
         'STUB_ODOM': '1', 'STUB_HARVEST': '1', 'STUB_SSH_RC': '0',
         'STUB_SSH_STARTS_SERVER': '1'}


def write_exe(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def run(tmp_path, **overrides):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir(exist_ok=True)
    write_exe(bin_dir / 'ros2', ROS2_STUB)
    write_exe(bin_dir / 'ssh', SSH_STUB)
    log = tmp_path / 'calls.log'
    log.write_text('')
    env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}',
               NILARM_ENV_SCRIPT='/dev/null', NILARM_READY_TIMEOUT='0',
               NILARM_LAPTOP_HOST='laptop.test', NILARM_LAPTOP_USER='tester',
               NILARM_SSH_KEY='/nonexistent', STUB_LOG=str(log),
               STUB_STARTED=str(tmp_path / 'started'), **READY)
    env.update(overrides)
    result = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True,
                            text=True, timeout=60)
    calls = log.read_text().splitlines()
    enables = [c for c in calls if c.startswith('ros2 service call /camera_drive/enable')]
    ssh = [c for c in calls if c.startswith('ssh ')]
    return result, enables, ssh


def test_all_ready_enables_exactly_once(tmp_path):
    result, enables, ssh = run(tmp_path)
    assert result.returncode == 0 and len(enables) == 1
    assert 'STARTED' in result.stdout


def test_server_already_on_graph_is_not_started_again(tmp_path):
    result, enables, ssh = run(tmp_path, STUB_HARVEST='1')
    assert ssh == [] and len(enables) == 1


def test_missing_server_is_started_over_batchmode_ssh(tmp_path):
    result, enables, ssh = run(tmp_path, STUB_HARVEST='0')
    assert len(ssh) == 1
    assert 'BatchMode=yes' in ssh[0] and 'StrictHostKeyChecking=yes' in ssh[0]
    assert 'tester@laptop.test' in ssh[0] and 'run_harvest_server.sh' in ssh[0]
    assert ssh[0].rstrip().endswith('start')
    assert result.returncode == 0 and len(enables) == 1


@pytest.mark.parametrize('ssh_rc', ['255', '1'])  # SSH/network/key fail, start fail
def test_remote_start_failure_never_enables(tmp_path, ssh_rc):
    result, enables, ssh = run(tmp_path, STUB_HARVEST='0', STUB_SSH_RC=ssh_rc)
    assert result.returncode == 1 and enables == []
    assert 'NOT STARTED' in result.stderr


def test_unconfigured_laptop_never_enables(tmp_path):
    result, enables, ssh = run(tmp_path, STUB_HARVEST='0', NILARM_LAPTOP_HOST='')
    assert result.returncode == 1 and enables == [] and ssh == []


def test_harvest_never_appears_never_enables(tmp_path):
    result, enables, ssh = run(tmp_path, STUB_HARVEST='0', STUB_SSH_STARTS_SERVER='0')
    assert len(ssh) == 1 and result.returncode == 1 and enables == []
    assert 'harvest_servers=0' in result.stderr


@pytest.mark.parametrize('missing', [
    {'STUB_DRIVES': '0'}, {'STUB_DRIVES': '2'}, {'STUB_DRIVES': '4'},
    {'STUB_SERVICE': '0'}, {'STUB_CAMERA': '0'}, {'STUB_ODOM': '0'},
    {'STUB_HARVEST': '2'}])
def test_any_missing_condition_never_enables(tmp_path, missing):
    result, enables, ssh = run(tmp_path, **missing)
    assert result.returncode == 1 and enables == []
    assert 'NOT STARTED' in result.stderr


def test_gives_up_when_launch_is_gone(tmp_path):
    result, enables, ssh = run(tmp_path, NILARM_LAUNCH_PID='999999999')
    assert result.returncode == 1 and enables == []


# --- laptop runner: never a second server -----------------------------------

def run_runner(tmp_path, server_running):
    """Copy of the runner in a temp repo. Stub `pgrep` fakes the process table
    (hermetic even if a real server runs); stub `setsid` records launches."""
    (tmp_path / 'scripts').mkdir()
    shutil.copy(RUNNER, tmp_path / 'scripts' / RUNNER.name)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    marker = tmp_path / 'launched'
    write_exe(bin_dir / 'setsid', f'#!/usr/bin/env bash\ntouch {marker}\n')
    write_exe(bin_dir / 'pgrep', '#!/usr/bin/env bash\n'
              + ('echo 4242\n' if server_running else 'exit 1\n'))
    env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}',
               DISPLAY=':99', NILARM_HARVEST_SETTLE_SEC='0.5')
    result = subprocess.run(
        ['bash', str(tmp_path / 'scripts' / RUNNER.name), 'start'],
        env=env, capture_output=True, text=True, timeout=60)
    return result, marker.exists()


def test_runner_does_not_start_second_server(tmp_path):
    result, launched = run_runner(tmp_path, server_running=True)
    assert result.returncode == 0 and not launched
    assert 'already running' in result.stdout


def test_runner_starts_when_absent_and_reports_early_exit(tmp_path):
    result, launched = run_runner(tmp_path, server_running=False)
    assert launched  # start attempted (stub setsid: nothing real runs)
    assert result.returncode == 1 and 'exited during startup' in result.stdout


def test_runner_pattern_matches_real_server_command_lines():
    text = RUNNER.read_text()
    pattern = text.split("pgrep -f -- '")[1].split("'")[0]

    def matches(cmdline):
        return subprocess.run(['grep', '-Eq', pattern], input=cmdline,
                              text=True).returncode == 0
    assert matches('python3 -m arm_control_pkg.pumpkin_harvest.harvest_action_server '
                   '--ros-args -p harvest_all_detected:=true')
    assert matches('/usr/bin/python3 /home/u/NILARM/install/arm_control_pkg/lib/'
                   'arm_control_pkg/harvest_action_server --ros-args')
    assert not matches('python3 -m arm_control_pkg.pumpkin_harvest.fake_harvest_action_server')
    assert not matches('bash /home/u/NILARM/scripts/run_harvest_server.sh start')
