"""Pinky `ksam_hsv_calibrate` -> camera -> SSH -> laptop, with stub ros2/ssh/pgrep/python.

No network, no GUI, no ROS, no camera: both scripts are copied into a
temporary repo so no real .nilarm_remote_env or YAML is ever read or written.
The stub camera records the signals it gets, so cleanup is checked for real.
    python3 -m pytest src/pinky_camera_drive/test/test_hsv_remote_launch.py
"""

import os
import pathlib
import re
import shutil
import signal
import stat
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]

SSH_STUB = r'''#!/usr/bin/env bash
printf '%s\n' "$@" > "$STUB_DIR/ssh_args"
pid="$(cat "$STUB_DIR/camera_pid" 2>/dev/null)"
[[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && touch "$STUB_DIR/camera_alive_at_ssh"
[[ -n "$STUB_SSH_SLEEP" ]] && sleep "$STUB_SSH_SLEEP"
if [[ "$STUB_SSH_RUN" == 1 ]]; then   # behave like the laptop: run the command
    HOME="$STUB_LAPTOP_HOME" exec bash -c "${@: -1}"
fi
exit "${STUB_SSH_RC:-0}"
'''
PGREP_STUB = r'''#!/usr/bin/env bash
pid="$STUB_PGREP_PID"
[[ "$*" == *camera_pkg/camera_publisher* ]] && pid="$STUB_CAMERA_PGREP"
[[ -n "$pid" ]] && echo "$pid"
[[ -n "$pid" ]]
'''
ROS2_STUB = r'''#!/usr/bin/env bash
echo "ros2 $*" >> "$STUB_DIR/ros2_calls"
case "$1 $2" in
  "topic echo")
    [[ "$STUB_FRAMES" == always ]] && exit 0
    [[ "$STUB_FRAMES" == after_start && -f "$STUB_DIR/camera_up" ]] && exit 0
    sleep 0.2; exit 124 ;;
  "run camera_pkg")
    echo "$$" > "$STUB_DIR/camera_pid"
    echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH" > "$STUB_DIR/camera_env"
    echo "LIBCAMERA_IPA_MODULE_PATH=$LIBCAMERA_IPA_MODULE_PATH" >> "$STUB_DIR/camera_env"
    [[ "$STUB_CAMERA_FAIL" == crash ]] && exit 1
    trap 'echo INT >> "$STUB_DIR/camera_signals"; exit 0' INT
    trap 'echo TERM >> "$STUB_DIR/camera_signals"; exit 0' TERM
    [[ "$STUB_CAMERA_FAIL" == noframes ]] || touch "$STUB_DIR/camera_up"
    while :; do sleep 0.05; done ;;
esac
'''
PY_STUB = r'''#!/usr/bin/env bash
if [[ "$1" == -c && "$2" == *ksam_hsv_probe* ]]; then exit "${STUB_PROBE_RC:-0}"; fi
[[ "$1" == -c ]] && exit 0                    # import rclpy check
echo "DISPLAY=$DISPLAY ROS_DOMAIN_ID=$ROS_DOMAIN_ID" > "$STUB_DIR/py_env"
printf '%s\n' "$@" > "$STUB_DIR/py_args"
echo "HSV CALIBRATION READY"
exit "${STUB_PY_RC:-0}"
'''


def write_exe(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def make_env(tmp_path):
    for name in ('start_remote_hsv_calibrate.sh', 'ksam_hsv_calibrate'):
        repo_script = tmp_path / 'laptop_home' / 'NILARM' / 'scripts' / name
        repo_script.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / 'scripts' / name, repo_script)
    pinky_repo = tmp_path / 'pinky_repo'
    (pinky_repo / 'scripts').mkdir(parents=True)
    shutil.copy(ROOT / 'scripts' / 'start_remote_hsv_calibrate.sh',
                pinky_repo / 'scripts')
    write_exe(tmp_path / 'bin' / 'ssh', SSH_STUB)
    write_exe(tmp_path / 'bin' / 'pgrep', PGREP_STUB)
    write_exe(tmp_path / 'bin' / 'ros2', ROS2_STUB)
    (tmp_path / 'pinky_home').mkdir()
    write_exe(tmp_path / 'py', PY_STUB)
    (tmp_path / 'x11').mkdir()
    env = {k: v for k, v in os.environ.items()
           if k not in ('DISPLAY', 'NILARM_LAPTOP_HOST', 'NILARM_LAPTOP_USER',
                        'ROS_DOMAIN_ID')}
    env.update(PATH=f"{tmp_path / 'bin'}:{os.environ['PATH']}",
               STUB_DIR=str(tmp_path), NILARM_SSH_KEY='/nonexistent',
               NILARM_HSV_PYTHON=str(tmp_path / 'py'),
               NILARM_X11_DIR=str(tmp_path / 'x11'),
               STUB_LAPTOP_HOME=str(tmp_path / 'laptop_home'),
               HOME=str(tmp_path / 'pinky_home'), NILARM_ENV_SCRIPT='/dev/null',
               STUB_FRAMES='always', NILARM_HSV_CAMERA_TIMEOUT='2')
    return env


def pinky(tmp_path, env, *args):
    return subprocess.run(
        ['bash', str(tmp_path / 'pinky_repo' / 'scripts' / 'start_remote_hsv_calibrate.sh'),
         *args], env=env, capture_output=True, text=True, timeout=30,
        stdin=subprocess.DEVNULL)


def laptop(tmp_path, env, *args):
    return subprocess.run(
        ['bash', str(tmp_path / 'laptop_home' / 'NILARM' / 'scripts' / 'ksam_hsv_calibrate'),
         *args], env=env, capture_output=True, text=True, timeout=30)


CONFIGURED = {'NILARM_LAPTOP_USER': 'fivejaewin', 'NILARM_LAPTOP_HOST': '172.20.10.2'}


def test_pinky_remote_command_construction(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED}, '--patch', '15', 'a b')
    assert result.returncode == 0
    args = (tmp_path / 'ssh_args').read_text().splitlines()
    assert args[-2] == 'fivejaewin@172.20.10.2'
    assert 'BatchMode=yes' in args and 'StrictHostKeyChecking=yes' in args
    assert 'ForwardX11=no' in args and '-T' in args  # no tty in tests
    assert args[-1] == ('ROS_DOMAIN_ID=99 bash "$HOME/NILARM/scripts/ksam_hsv_calibrate"'
                        r' --patch 15 a\ b')


def test_pinky_uses_remote_harvest_config_file(tmp_path):
    env = make_env(tmp_path)
    (tmp_path / 'pinky_repo' / '.nilarm_remote_env').write_text(
        'NILARM_LAPTOP_USER=fivejaewin\nNILARM_LAPTOP_HOST=192.168.4.2\n')
    assert pinky(tmp_path, env).returncode == 0
    assert (tmp_path / 'ssh_args').read_text().splitlines()[-2] == 'fivejaewin@192.168.4.2'


def test_pinky_not_configured(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, env)
    assert result.returncode == 20 and 'not configured' in result.stderr
    assert not (tmp_path / 'ssh_args').exists()


def test_pinky_laptop_unreachable(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_SSH_RC': '255'})
    assert result.returncode == 21
    assert 'cannot reach laptop fivejaewin@172.20.10.2' in result.stderr


def test_pinky_passes_laptop_result_through(tmp_path):
    env = make_env(tmp_path)
    for rc in (1, 4, 10, 11):
        assert pinky(tmp_path, {**env, **CONFIGURED, 'STUB_SSH_RC': str(rc)}).returncode == rc


def test_laptop_missing_display(tmp_path):
    env = make_env(tmp_path)  # empty X11 dir, DISPLAY unset
    result = laptop(tmp_path, env)
    assert result.returncode == 10
    assert 'HSV calibration NOT started: laptop desktop DISPLAY unavailable' in result.stderr
    assert not (tmp_path / 'py_args').exists()


def test_laptop_display_probe_fails(tmp_path):
    env = make_env(tmp_path)
    (tmp_path / 'x11' / 'X0').touch()
    (tmp_path / 'home').mkdir()
    (tmp_path / 'home' / '.Xauthority').touch()
    result = laptop(tmp_path, {**env, 'HOME': str(tmp_path / 'home'), 'STUB_PROBE_RC': '1'})
    assert result.returncode == 10 and 'DISPLAY unavailable' in result.stderr


def test_laptop_duplicate_calibrator(tmp_path):
    env = make_env(tmp_path)
    result = laptop(tmp_path, {**env, 'DISPLAY': ':0', 'STUB_PGREP_PID': '4242'})
    assert result.returncode == 11
    assert 'already running on the laptop (pid 4242)' in result.stderr
    assert not (tmp_path / 'py_args').exists()


def test_laptop_direct_run_keeps_display(tmp_path):
    env = make_env(tmp_path)
    result = laptop(tmp_path, {**env, 'DISPLAY': ':5', 'STUB_PY_RC': '4'}, '--no-deploy')
    assert result.returncode == 4
    args = (tmp_path / 'py_args').read_text().splitlines()
    assert args[:3] == ['-u', '-m', 'pinky_camera_drive.hsv_calibrator']
    assert args[-1] == '--no-deploy'
    assert 'DISPLAY=:5 ' in (tmp_path / 'py_env').read_text()


def test_full_pinky_to_laptop_success(tmp_path):
    env = make_env(tmp_path)
    (tmp_path / 'x11' / 'X1').touch()
    (tmp_path / 'laptop_home' / '.Xauthority').touch()
    result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_SSH_RUN': '1'}, '--patch', '9')
    assert result.returncode == 0, result.stderr
    assert 'HSV CALIBRATION READY' in result.stdout
    assert 'DISPLAY=:1 ROS_DOMAIN_ID=99' in (tmp_path / 'py_env').read_text()
    args = (tmp_path / 'py_args').read_text().splitlines()
    assert args[-2:] == ['--patch', '9']
    assert args[args.index('--config') + 1].endswith(
        'laptop_home/NILARM/src/pinky_camera_drive/config/camera_straight_drive.yaml')


# ------------------------------------------------------------ Pinky camera --

def read(tmp_path, name):
    path = tmp_path / name
    return path.read_text() if path.exists() else ''


def camera_started(tmp_path):
    return 'ros2 run camera_pkg camera_publisher' in read(tmp_path, 'ros2_calls')


def assert_camera_stopped(tmp_path):
    assert read(tmp_path, 'camera_signals').startswith('INT')  # clean ROS shutdown
    pid = int(read(tmp_path, 'camera_pid'))
    for _ in range(50):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    raise AssertionError(f'camera pid {pid} still alive')


def test_camera_already_publishing_is_reused(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED})
    assert result.returncode == 0
    assert 'Pinky camera already running' in result.stdout
    assert not camera_started(tmp_path)
    assert (tmp_path / 'ssh_args').exists()


def test_camera_started_then_stopped_after_success(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_FRAMES': 'after_start'})
    assert result.returncode == 0, result.stderr
    for line in ('starting Pinky camera...', 'waiting for /camera/image/compressed...',
                 'Pinky camera ready', 'opening on laptop'):
        assert line in result.stdout
    assert camera_started(tmp_path)
    assert (tmp_path / 'camera_alive_at_ssh').exists()  # frames before laptop GUI
    env_lines = read(tmp_path, 'camera_env')
    assert 'LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:/opt/ros/jazzy/lib:' in env_lines
    assert 'LIBCAMERA_IPA_MODULE_PATH=/usr/local/lib/aarch64-linux-gnu/libcamera' in env_lines
    assert 'ksam_hsv_calibrate camera start' in read(
        tmp_path, 'pinky_home/.nilarm_logs/hsv_camera.log')
    assert_camera_stopped(tmp_path)


def test_camera_env_matches_competition_launch():
    launch = (ROOT / 'src/nilarm_bringup/launch/competition.launch.py').read_text()
    script = (ROOT / 'scripts/start_remote_hsv_calibrate.sh').read_text()
    lib = re.search(r"CAMERA_LIB = '([^']+)'", launch).group(1)
    assert f'CAMERA_LIB={lib}\n' in script
    assert "CAMERA_LIB + '/libcamera'" in launch and '${CAMERA_LIB}/libcamera' in script


def test_camera_crash_does_not_start_laptop(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_FRAMES': 'after_start',
                              'STUB_CAMERA_FAIL': 'crash'})
    assert result.returncode == 22
    assert 'HSV calibration NOT started: Pinky camera failed to start' in result.stderr
    assert not (tmp_path / 'ssh_args').exists()


def test_camera_without_frames_times_out_and_is_stopped(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_FRAMES': 'after_start',
                              'STUB_CAMERA_FAIL': 'noframes'})
    assert result.returncode == 22
    assert 'Pinky camera failed to start' in result.stderr
    assert not (tmp_path / 'ssh_args').exists()
    assert_camera_stopped(tmp_path)


def test_stale_camera_process_no_duplicate(tmp_path):
    env = make_env(tmp_path)
    result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_FRAMES': 'never',
                              'STUB_CAMERA_PGREP': '777'})
    assert result.returncode == 23
    assert 'pid 777' in result.stderr and 'not starting a duplicate' in result.stderr
    assert not camera_started(tmp_path)
    assert not (tmp_path / 'ssh_args').exists()


def test_cancel_and_exit_codes_stop_own_camera(tmp_path):
    for rc in (1, 4):  # cancelled, deploy failed
        sub = tmp_path / str(rc)
        sub.mkdir()
        env = make_env(sub)
        result = pinky(sub, {**env, **CONFIGURED, 'STUB_FRAMES': 'after_start',
                             'STUB_SSH_RC': str(rc)})
        assert result.returncode == rc
        assert_camera_stopped(sub)


def test_preexisting_camera_is_not_killed(tmp_path):
    env = make_env(tmp_path)
    other = subprocess.Popen(['sleep', '30'])
    try:
        result = pinky(tmp_path, {**env, **CONFIGURED, 'STUB_CAMERA_PGREP': str(other.pid),
                                  'STUB_SSH_RC': '1'})
        assert result.returncode == 1
        assert 'stopping' not in result.stdout
        assert other.poll() is None
    finally:
        other.kill()
        other.wait()


def test_ctrl_c_stops_own_camera(tmp_path):
    env = make_env(tmp_path)
    proc = subprocess.Popen(
        ['bash', str(tmp_path / 'pinky_repo' / 'scripts' / 'start_remote_hsv_calibrate.sh')],
        env={**env, **CONFIGURED, 'STUB_FRAMES': 'after_start', 'STUB_SSH_SLEEP': '30'},
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True)
    deadline = time.monotonic() + 20
    while not (tmp_path / 'ssh_args').exists():
        assert time.monotonic() < deadline and proc.poll() is None
        time.sleep(0.05)
    os.killpg(proc.pid, signal.SIGINT)  # what the terminal does on Ctrl+C
    out, _ = proc.communicate(timeout=20)
    assert proc.returncode == 130
    assert 'stopping the Pinky camera' in out
    assert_camera_stopped(tmp_path)
