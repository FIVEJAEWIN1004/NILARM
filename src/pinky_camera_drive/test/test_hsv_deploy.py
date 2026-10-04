"""hsv_deploy tests without a real Pinky.

The fake runner executes the real remote shell script locally against a
temporary $HOME, so backup/checksum/mv/verify are exercised for real.
    python3 -m pytest src/pinky_camera_drive/test/test_hsv_deploy.py
"""

import datetime
import os
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pinky_camera_drive import hsv_deploy as hd  # noqa: E402

YAML = """camera_straight_drive:
  ros__parameters:
    kp: 0.002
    yellow_h_low: {h}
    yellow_h_high: 35
    yellow_s_low: 100
    yellow_s_high: 190
    yellow_v_low: 80
    yellow_v_high: 220
"""
NOW = datetime.datetime(2026, 10, 4, 12, 0, 0)


def test_env_file_parsing(tmp_path):
    env = tmp_path / '.nilarm_pinky_env'
    assert hd.read_env_file(env) is None  # missing file
    env.write_text('# comment\nOTHER=x\nexport NILARM_PINKY_HOST="pinky@192.168.4.1"  # comp\n')
    assert hd.read_env_file(env) == 'pinky@192.168.4.1'
    env.write_text('NILARM_PINKY_HOST=\n')
    assert hd.read_env_file(env) is None


def test_host_resolution_order(tmp_path):
    env = tmp_path / '.nilarm_pinky_env'
    assert hd.resolve_host({}, env) == ('pinky@172.20.10.3', 'built-in default')
    env.write_text('NILARM_PINKY_HOST=pinky@192.168.4.1\n')
    assert hd.resolve_host({}, env) == ('pinky@192.168.4.1', str(env))
    # Environment variable overrides the file.
    host, source = hd.resolve_host({'NILARM_PINKY_HOST': 'pinky@10.0.0.7'}, env)
    assert (host, source) == ('pinky@10.0.0.7', '$NILARM_PINKY_HOST')
    assert hd.resolve_host({'NILARM_PINKY_HOST': '  '}, env)[0] == 'pinky@192.168.4.1'
    for bad in ('-oProxyCommand=x', 'pinky@host;rm -rf', 'a b'):
        with pytest.raises(ValueError):
            hd.resolve_host({'NILARM_PINKY_HOST': bad}, env)


def test_remote_paths_and_commands():
    cfg, tmp, bak = hd.remote_paths('20261004_120000')
    assert cfg == 'NILARM/src/pinky_camera_drive/config/camera_straight_drive.yaml'
    assert tmp == ('NILARM/src/pinky_camera_drive/config/'
                   '.camera_straight_drive.yaml.hsv_upload_20261004_120000')
    assert bak == cfg + '.bak_hsv_20261004_120000'
    assert not tmp.endswith('.yaml')  # setup.py glob('config/*.yaml') ignores it
    scp = hd.scp_cmd('pinky@h', '/c/cm', '/l/x.yaml', tmp)
    assert scp[0] == 'scp' and scp[-2:] == ['/l/x.yaml', 'pinky@h:' + tmp]
    assert 'ControlPath=/c/cm' in scp
    ssh = hd.ssh_cmd('pinky@h', '/c/cm', 'sh -s')
    assert ssh[0] == 'ssh' and ssh[-2:] == ['pinky@h', 'sh -s']
    script = hd.replace_script(cfg, tmp, bak, 'abc')
    assert script.index('cp -p') < script.index('mv -f')  # backup before replace


def test_verification_logic():
    local = YAML.format(h=25)
    ok, _ = hd.verify_remote_output(hd.REPLACED_MARKER + '\n' + local, local)
    assert ok
    ok, reason = hd.verify_remote_output(
        hd.REPLACED_MARKER + '\n' + YAML.format(h=22), local)
    assert not ok and 'yellow_h_low=22' in reason
    ok, _ = hd.verify_remote_output(local, local)  # no marker -> not replaced
    assert not ok
    assert hd.non_hsv_differences(YAML.format(h=22), local) == []
    assert hd.non_hsv_differences(
        YAML.format(h=22).replace('kp: 0.002', 'kp: 0.003'), local) == ['kp']


def fake_runner(home, fail=None):
    """Run ssh/scp commands locally against home instead of a Pinky."""
    calls = []

    def run(cmd, input=None, **kwargs):
        calls.append(cmd)
        if fail and fail(cmd):
            return SimpleNamespace(returncode=255, stdout='', stderr='unreachable')
        if cmd[0] == 'ssh' and '-O' in cmd:
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        if cmd[0] == 'scp':
            shutil.copy(cmd[-2], home / cmd[-1].split(':', 1)[1])
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        return subprocess.run(['sh', '-c', cmd[-1]], input=input, cwd=home,
                              env={**os.environ, 'HOME': str(home)},
                              capture_output=True, text=True)
    run.calls = calls
    return run


@pytest.fixture
def pinky(tmp_path):
    home = tmp_path / 'pinky_home'
    cfg = home / hd.REMOTE_CONFIG
    cfg.parent.mkdir(parents=True)
    cfg.write_text(YAML.format(h=22))
    local = tmp_path / 'laptop.yaml'
    local.write_text(YAML.format(h=25))
    return home, cfg, local


def test_deploy_success(pinky):
    home, cfg, local = pinky
    ok, reason = hd.deploy(local, 'pinky@h', run=fake_runner(home),
                           log=lambda m: None, now=NOW)
    assert ok, reason
    assert cfg.read_text() == local.read_text()
    backup = cfg.parent / 'camera_straight_drive.yaml.bak_hsv_20261004_120000'
    assert backup.read_text() == YAML.format(h=22)
    assert sorted(p.name for p in cfg.parent.iterdir()) == [
        'camera_straight_drive.yaml', backup.name]  # temp file gone


def test_unreachable_or_upload_failure_leaves_pinky(pinky):
    home, cfg, local = pinky
    for fail in (lambda c: c[0] == 'ssh', lambda c: c[0] == 'scp'):
        ok, reason = hd.deploy(local, 'pinky@h', run=fake_runner(home, fail),
                               log=lambda m: None, now=NOW)
        assert not ok
        assert cfg.read_text() == YAML.format(h=22)
        assert os.listdir(cfg.parent) == ['camera_straight_drive.yaml']


def test_non_hsv_difference_refused(pinky):
    home, cfg, local = pinky
    cfg.write_text(YAML.format(h=22).replace('kp: 0.002', 'kp: 0.009'))
    run = fake_runner(home)
    ok, reason = hd.deploy(local, 'pinky@h', run=run, log=lambda m: None, now=NOW)
    assert not ok and 'kp' in reason
    assert not any(c[0] == 'scp' for c in run.calls)


def test_corrupt_upload_refused(pinky):
    home, cfg, local = pinky
    base = fake_runner(home)

    def run(cmd, **kwargs):
        result = base(cmd, **kwargs)
        if cmd[0] == 'scp':  # truncate what "arrived" on Pinky
            (home / cmd[-1].split(':', 1)[1]).write_text('garbage')
        return result
    ok, reason = hd.deploy(local, 'pinky@h', run=run, log=lambda m: None, now=NOW)
    assert not ok and 'checksum' in reason
    assert cfg.read_text() == YAML.format(h=22)
    assert os.listdir(cfg.parent) == ['camera_straight_drive.yaml']
