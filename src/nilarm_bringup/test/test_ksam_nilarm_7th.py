"""ksam_nilarm_7th (Pinky) + laptop runner build/restart, fully stubbed.

`ssh`, `nilarm`, `ros2`, `colcon`, `pgrep` and `setsid` are stubs; the only
processes ever signalled are `sleep` dummies this test starts itself. No SSH,
ROS graph, OMX, camera or motor is touched.
"""

import os
import pathlib
import re
import shutil
import signal
import stat
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
KSAM = ROOT / 'scripts' / 'ksam_nilarm_7th'
RUNNER = ROOT / 'scripts' / 'run_harvest_server.sh'
SETUP = ROOT / 'scripts' / 'setup_pinky.sh'
HARVEST = ROOT / 'src' / 'arm_control_pkg' / 'arm_control_pkg' / 'pumpkin_harvest'


def write_exe(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


# --- Pinky side: ksam_nilarm_7th ---------------------------------------------

SSH_STUB = r'''#!/usr/bin/env bash
echo "ssh $*" >> "$STUB_LOG"
case "${@: -1}" in
  true) exit "${STUB_CONNECT_RC:-0}" ;;
  *" build") exit "${STUB_BUILD_RC:-0}" ;;
  *" restart") exit "${STUB_RESTART_RC:-0}" ;;
esac
exit 99
'''
NILARM_STUB = r'''#!/usr/bin/env bash
echo "nilarm ROS_DOMAIN_ID=$ROS_DOMAIN_ID args=$*" >> "$STUB_LOG"
'''


def run_ksam(tmp_path, remote_env='NILARM_LAPTOP_USER=lapuser\nNILARM_LAPTOP_HOST=10.9.8.7\n',
             **overrides):
    repo = tmp_path / 'repo'
    (repo / 'scripts').mkdir(parents=True)
    shutil.copy(KSAM, repo / 'scripts' / KSAM.name)
    write_exe(repo / 'src' / 'nilarm_bringup' / 'scripts' / 'nilarm', NILARM_STUB)
    if remote_env is not None:
        (repo / '.nilarm_remote_env').write_text(remote_env)
    write_exe(tmp_path / 'bin' / 'ssh', SSH_STUB)
    log = tmp_path / 'calls.log'
    log.write_text('')
    env = {k: v for k, v in os.environ.items() if not k.startswith('NILARM_')}
    env.update(PATH=f'{tmp_path / "bin"}:{os.environ["PATH"]}', STUB_LOG=str(log),
               NILARM_SSH_KEY='/nonexistent', ROS_DOMAIN_ID='7')
    env.update(overrides)
    result = subprocess.run(['bash', str(repo / 'scripts' / KSAM.name), '--x'],
                            env=env, capture_output=True, text=True, timeout=30)
    result.calls = log.read_text().splitlines()
    result.nilarm = [c for c in result.calls if c.startswith('nilarm ')]
    return result


def test_is_a_pinky_command_that_execs_repo_nilarm():
    text = KSAM.read_text()
    assert text.splitlines()[1].startswith('# PINKY')
    assert 'exec "${repo}/src/nilarm_bringup/scripts/nilarm" "$@"' in text
    assert 'colcon' not in text  # the build runs on the laptop, over SSH


def test_success_builds_then_restarts_then_execs_nilarm(tmp_path):
    result = run_ksam(tmp_path)
    assert result.returncode == 0, result.stderr
    kinds = [c.split()[-1] if c.startswith('ssh') else 'nilarm' for c in result.calls]
    assert kinds == ['true', 'build', 'restart', 'nilarm']
    assert result.nilarm == ['nilarm ROS_DOMAIN_ID=99 args=--x']
    for line in ('노트북 SSH 연결 확인', '노트북 최신 로봇팔 코드 빌드', '기존 수확 서버 재시작',
                 '/harvest 서버 준비 완료', 'Pinky competition launch 시작'):
        assert f'[KSAM 7TH] {line}' in result.stdout


def test_reuses_nilarm_remote_env_and_domain_99(tmp_path):
    result = run_ksam(tmp_path)
    ssh = [c for c in result.calls if c.startswith('ssh')]
    assert all('lapuser@10.9.8.7' in c for c in ssh)
    assert all('BatchMode=yes' in c and 'StrictHostKeyChecking=yes' in c for c in ssh)
    assert 'ROS_DOMAIN_ID=99 bash "$HOME/NILARM/scripts/run_harvest_server.sh" build' in ssh[1]
    assert 'ROS_DOMAIN_ID=99' in ssh[2]
    assert not re.search(r'\d+\.\d+\.\d+\.\d+|@\w', KSAM.read_text())  # nothing hardcoded


@pytest.mark.parametrize('stub,message', [
    ({'STUB_CONNECT_RC': '255'}, '노트북 SSH 연결 실패'),
    ({'STUB_BUILD_RC': '1'}, '노트북 원격 빌드 실패'),
    ({'STUB_BUILD_RC': '127'}, '노트북 NILARM 작업공간 없음'),
    ({'STUB_BUILD_RC': '255'}, 'SSH 연결 끊김'),
    ({'STUB_RESTART_RC': '1'}, '/harvest 준비 확인 실패'),
    ({'STUB_RESTART_RC': '255'}, 'SSH 연결 끊김'),
])
def test_any_laptop_failure_never_launches_pinky(tmp_path, stub, message):
    result = run_ksam(tmp_path, **stub)
    assert result.returncode == 1 and result.nilarm == []
    assert message in result.stderr and '주행을 시작하지 않습니다' in result.stderr


def test_build_failure_never_restarts_server(tmp_path):
    result = run_ksam(tmp_path, STUB_BUILD_RC='1')
    assert not any(c.endswith(' restart') for c in result.calls)


def test_unconfigured_laptop_never_sshs_or_launches(tmp_path):
    result = run_ksam(tmp_path, remote_env=None)
    assert result.returncode == 1 and result.calls == []
    assert '노트북 접속 설정 없음' in result.stderr


def test_setup_pinky_installs_the_command_link():
    assert ('ln -sfn "${repo}/scripts/ksam_nilarm_7th" "$HOME/.local/bin/ksam_nilarm_7th"'
            in SETUP.read_text())


@pytest.mark.parametrize('script', [KSAM, RUNNER, SETUP])
def test_shell_syntax(script):
    assert subprocess.run(['bash', '-n', str(script)]).returncode == 0


# --- Laptop side: run_harvest_server.sh build / restart ----------------------

@pytest.fixture
def laptop(tmp_path):
    """Temp repo copy of the runner; stub activate/ros2/colcon/pgrep/setsid."""
    repo = tmp_path / 'repo'
    (repo / 'scripts').mkdir(parents=True)
    shutil.copy(RUNNER, repo / 'scripts' / RUNNER.name)
    (repo / 'scripts' / 'activate_pumpkin_harvest.sh').write_text(
        'echo "activate ROS_DOMAIN_ID=$ROS_DOMAIN_ID" >> "$STUB_LOG"\n')
    (repo / 'install').mkdir()
    (repo / 'install' / 'setup.bash').write_text('')
    home = tmp_path / 'home'
    (home / 'venv' / 'omx' / 'bin').mkdir(parents=True)
    (home / 'venv' / 'omx' / 'bin' / 'activate').write_text('')
    bin_dir = tmp_path / 'bin'
    # pgrep: the "server" is whatever pids in $STUB_SERVERS are still alive.
    write_exe(bin_dir / 'pgrep', '#!/usr/bin/env bash\nfound=1\n'
              'for p in $STUB_SERVERS; do kill -0 $p 2>/dev/null && echo $p && found=0; done\n'
              'exit $found\n')
    spawned = tmp_path / 'spawned'
    write_exe(bin_dir / 'setsid', '#!/usr/bin/env bash\necho "setsid $*" >> "$STUB_LOG"\n'
              f'echo $$ >> {spawned}\nexec sleep 30\n')
    write_exe(bin_dir / 'colcon', '#!/usr/bin/env bash\necho "colcon $* '
              'ROS_DOMAIN_ID=$ROS_DOMAIN_ID" >> "$STUB_LOG"\nexit ${STUB_COLCON_RC:-0}\n')
    write_exe(bin_dir / 'ros2', '#!/usr/bin/env bash\necho "ros2 $*" >> "$STUB_LOG"\n'
              'echo "Action servers: ${STUB_HARVEST:-1}"\n')
    write_exe(bin_dir / 'pkill', '#!/usr/bin/env bash\necho "pkill $*" >> "$STUB_LOG"\n')
    log = tmp_path / 'calls.log'
    log.write_text('')
    dummies = []

    def dummy(ignore_term=False):
        # Detached like the real server (reparented to init, so it is reaped).
        body = "trap '' TERM; while :; do sleep 0.1; done" if ignore_term else 'exec sleep 300'
        pid = int(subprocess.run(['bash', '-c', f'bash -c "{body}" >/dev/null 2>&1 & echo $!'],
                                 capture_output=True, text=True).stdout)
        dummies.append(pid)
        return pid

    def run(command, servers=(), pid_file=None, **overrides):
        logs = repo / '.nilarm_logs'
        logs.mkdir(exist_ok=True)
        log.write_text('')
        if pid_file is not None:
            (logs / 'harvest_server.pid').write_text(f'{pid_file}\n')
        env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}', HOME=str(home),
                   STUB_LOG=str(log), STUB_SERVERS=' '.join(map(str, servers)),
                   DISPLAY=':99', ROS_DOMAIN_ID='99', NILARM_HARVEST_SETTLE_SEC='0.3',
                   NILARM_HARVEST_STOP_SEC='2', NILARM_HARVEST_READY_SEC='0')
        env.update(overrides)
        result = subprocess.run(['bash', str(repo / 'scripts' / RUNNER.name), command],
                                env=env, capture_output=True, text=True, timeout=60)
        result.calls = log.read_text().splitlines()
        for pid in (spawned.read_text().split() if spawned.exists() else []):
            try:
                os.kill(int(pid), signal.SIGKILL)  # the stub "server" sleep
            except ProcessLookupError:
                pass
        return result

    run.dummy = dummy
    run.home = home
    yield run
    for pid in dummies:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True,
                          text=True).stdout.strip()[:1] not in ('Z', '')


def test_build_runs_colcon_up_to_arm_control_pkg_in_omx_env(laptop):
    result = laptop('build')
    assert result.returncode == 0 and 'OK: arm_control_pkg built' in result.stdout
    colcon = [c for c in result.calls if c.startswith('colcon')]
    assert colcon == ['colcon build --packages-up-to arm_control_pkg --symlink-install '
                      'ROS_DOMAIN_ID=99']
    assert result.calls[0].startswith('activate') and result.calls[1] == colcon[0]


def test_build_failure_and_missing_venv_fail(laptop):
    assert laptop('build', STUB_COLCON_RC='2').returncode == 1
    (laptop.home / 'venv' / 'omx' / 'bin' / 'activate').unlink()
    result = laptop('build')
    assert result.returncode == 1 and 'OMX venv missing' in result.stdout
    assert not any(c.startswith('colcon') for c in result.calls)


def test_restart_terms_exactly_the_pid_file_server_then_starts_new(laptop):
    old = laptop.dummy()
    other = laptop.dummy()  # an unrelated process: must survive
    result = laptop('restart', servers=[old], pid_file=old)
    assert result.returncode == 0, result.stdout
    assert f'stopping harvest server pid {old} (PID file verified)' in result.stdout
    assert not alive(old) and alive(other)
    assert sum(c.startswith('setsid') for c in result.calls) == 1
    assert '-m arm_control_pkg.pumpkin_harvest.harvest_action_server' in '\n'.join(result.calls)
    assert any(c == 'ros2 action info /harvest' for c in result.calls)
    assert 'OK: /harvest ready' in result.stdout and '.nilarm_logs/harvest_server.log' in result.stdout
    assert not any(c.startswith('pkill') for c in result.calls)


def test_restart_without_pid_file_uses_exact_matched_pid(laptop):
    old = laptop.dummy()
    result = laptop('restart', servers=[old], pid_file=123456789)
    assert result.returncode == 0 and not alive(old)
    assert 'exact cmdline match' in result.stdout


def test_restart_with_no_server_just_starts_one(laptop):
    result = laptop('restart')
    assert result.returncode == 0
    assert sum(c.startswith('setsid') for c in result.calls) == 1


def test_restart_refuses_duplicate_servers(laptop):
    a, b = laptop.dummy(), laptop.dummy()
    result = laptop('restart', servers=[a, b], pid_file=a)
    assert result.returncode == 1 and '2 harvest servers running' in result.stdout
    assert alive(a) and alive(b)
    assert not any(c.startswith('setsid') for c in result.calls)


def test_restart_stop_failure_never_starts_second_server(laptop):
    stubborn = laptop.dummy(ignore_term=True)
    result = laptop('restart', servers=[stubborn], pid_file=stubborn)
    assert result.returncode == 1 and 'did not exit after SIGTERM' in result.stdout
    assert not any(c.startswith('setsid') for c in result.calls)


@pytest.mark.parametrize('servers', ['0', '2'])
def test_restart_fails_unless_exactly_one_harvest_server(laptop, servers):
    result = laptop('restart', STUB_HARVEST=servers)
    assert result.returncode == 1 and '/harvest not ready' in result.stdout


# --- the restarted server runs the current v5 -> v4 -> v2 arm code ------------

def test_server_entry_runs_v5_v4_v2_chain():
    server = (HARVEST / 'harvest_action_server.py').read_text()
    v5 = (HARVEST / 'pumpkin_full_auto_orange_harvest_to_bin_v5.py').read_text()
    runner = RUNNER.read_text()
    assert 'python3 -m arm_control_pkg.pumpkin_harvest.harvest_action_server' in runner
    assert 'from .pumpkin_full_auto_orange_harvest_to_bin_v5 import run_harvest' in server
    assert 'v4.configure_selective_speed()' in v5
    assert 'return v2.harvest_one_direct(' in v5 and 'scan.harvest_one = harvest_one' in v5
    assert 'v2.deposit_and_prepare_next = v4.deposit_open_then_rise' in v5


def test_current_speed_direct_and_release_settings():
    v2 = (HARVEST / 'pumpkin_full_auto_orange_harvest_to_bin_v2.py').read_text()
    v4 = (HARVEST / 'pumpkin_full_auto_orange_harvest_to_bin_v4.py').read_text()
    assert 'FINAL_APPROACH_DURATIONS_SEC = (2.5, 2.0, 2.0)' in v2  # ⑬
    assert 'LIFT_EARLY_MIN_DURATION_SEC = 0.50' in v2  # ⑮
    assert 'DIRECT_NEXT_TARGET_FROM_BIN_HOVER = True' in v4
    assert 'DIRECT_HOVER_BYPASS_APPROACH_DELTA_GUARD = True' in v4
    assert 'PARK_MIN_DURATION_SEC = 1.5' in v4  # ㉒
