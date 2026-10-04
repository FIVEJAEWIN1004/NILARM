"""Copy the calibrated camera_straight_drive.yaml (only that file) to Pinky.

Pinky target, first match wins:
  1. $NILARM_PINKY_HOST
  2. NILARM_PINKY_HOST=... in <repo>/.nilarm_pinky_env (git-ignored)
  3. DEFAULT_PINKY_HOST
Flow: read remote YAML (refuse if any non-HSV key differs) -> scp to a hidden
temp name -> on Pinky: checksum, backup, atomic mv -> verify the six yellow_*
values and checksum of the file now on Pinky. Never runs anything else there.
"""

import datetime
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from pinky_camera_drive.hsv_utils import HSV_KEYS

DEFAULT_PINKY_HOST = 'pinky@172.20.10.3'  # the only place the address lives
HOST_ENV = 'NILARM_PINKY_HOST'
ENV_FILE_NAME = '.nilarm_pinky_env'
REPO_ROOT = Path(__file__).resolve().parents[3]
# Relative to the Pinky user's home (ssh/scp start there).
REMOTE_CONFIG = 'NILARM/src/pinky_camera_drive/config/camera_straight_drive.yaml'
NODE = 'camera_straight_drive'
REPLACED_MARKER = 'HSV_DEPLOY_REPLACED'
_HOST_RE = re.compile(r'^(?:[A-Za-z0-9._-]+@)?[A-Za-z0-9][A-Za-z0-9._-]*$')


def read_env_file(path):
    """Return NILARM_PINKY_HOST from a KEY=VALUE file (not sourced), or None."""
    try:
        lines = Path(path).read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return None
    value = None
    for line in lines:
        line = line.strip()
        if line.startswith('export '):
            line = line[len('export '):].strip()
        key, sep, raw = line.partition('=')
        if sep and key.strip() == HOST_ENV:
            value = raw.split('#', 1)[0].strip().strip('"\'') or None
    return value


def resolve_host(environ=None, env_file=None):
    """Return (host, source) following env var > env file > default."""
    environ = os.environ if environ is None else environ
    env_file = REPO_ROOT / ENV_FILE_NAME if env_file is None else Path(env_file)
    candidates = (
        (environ.get(HOST_ENV, '').strip(), f'${HOST_ENV}'),
        (read_env_file(env_file), str(env_file)),
        (DEFAULT_PINKY_HOST, 'built-in default'),
    )
    for host, source in candidates:
        if host:
            if not _HOST_RE.match(host):
                raise ValueError(f'invalid Pinky host {host!r} from {source}')
            return host, source
    raise AssertionError('unreachable')


def remote_paths(stamp, config=REMOTE_CONFIG):
    """Return (config, temp_upload, backup) remote paths for one deploy."""
    directory, name = config.rsplit('/', 1)
    return (config,
            f'{directory}/.{name}.hsv_upload_{stamp}',
            f'{config}.bak_hsv_{stamp}')


def ssh_options(control_path):
    # One connection (one password prompt at most) shared by every step.
    return ['-o', 'ConnectTimeout=5',
            '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2',
            '-o', 'ControlMaster=auto', '-o', f'ControlPath={control_path}',
            '-o', 'ControlPersist=60']


def ssh_cmd(host, control_path, remote_command):
    return ['ssh', *ssh_options(control_path), host, remote_command]


def scp_cmd(host, control_path, local_path, remote_path):
    return ['scp', '-q', *ssh_options(control_path),
            str(local_path), f'{host}:{remote_path}']


def replace_script(config, temp, backup, sha256):
    """POSIX sh run on Pinky (stdin of `sh -s`): check, backup, atomic mv."""
    q = shlex.quote
    return f"""set -eu
cd "$HOME"
cfg={q(config)}; tmp={q(temp)}; bak={q(backup)}
trap 'rm -f "$tmp"' EXIT
fail() {{ echo "HSV_DEPLOY_ERROR $*"; exit 20; }}
[ -f "$cfg" ] || fail "missing $cfg"
[ "$(sha256sum "$tmp" | cut -d' ' -f1)" = {q(sha256)} ] || fail "upload checksum mismatch"
[ ! -e "$bak" ] || fail "backup $bak already exists"
cp -p "$cfg" "$bak"
cmp -s "$cfg" "$bak" || fail "backup verify failed"
chmod --reference="$cfg" "$tmp"
mv -f "$tmp" "$cfg"
echo {REPLACED_MARKER}
cat "$cfg"
"""


def params_of(text):
    return yaml.safe_load(text)[NODE]['ros__parameters']


def non_hsv_differences(remote_text, local_text):
    """Keys (other than the six yellow_*) whose values differ or are missing."""
    remote, local = params_of(remote_text), params_of(local_text)
    keys = (set(remote) | set(local)) - set(HSV_KEYS)
    return sorted(k for k in keys if remote.get(k, '<missing>') != local.get(k, '<missing>'))


def verify_remote_output(stdout, local_text):
    """Return (ok, reason) for the replace step's output vs the local file."""
    marker = REPLACED_MARKER + '\n'
    if marker not in stdout:
        return False, 'remote replace did not complete'
    remote_text = stdout.split(marker, 1)[1]
    try:
        remote = params_of(remote_text)
    except Exception as exc:  # noqa: BLE001
        return False, f'remote YAML unreadable: {exc}'
    local = params_of(local_text)
    wrong = [k for k in HSV_KEYS if remote.get(k) != local[k]]
    if wrong:
        return False, 'remote values differ: ' + ', '.join(
            f'{k}={remote.get(k)} (want {local[k]})' for k in wrong)
    if hashlib.sha256(remote_text.encode()).hexdigest() != \
            hashlib.sha256(local_text.encode()).hexdigest():
        return False, 'remote file content differs from laptop file'
    return True, 'six yellow_* values and file checksum match'


def deploy(local_path, host, run=subprocess.run, log=print, now=None):
    """Deploy local_path to host. Return (ok, reason); never raises on SSH errors."""
    local_text = Path(local_path).read_text(encoding='utf-8')
    sha = hashlib.sha256(local_text.encode()).hexdigest()
    stamp = (now or datetime.datetime.now()).strftime('%Y%m%d_%H%M%S')
    config, temp, backup = remote_paths(stamp)
    control_dir = tempfile.mkdtemp(prefix='nilarm_ssh_')
    control = os.path.join(control_dir, 'cm')

    def call(cmd, **kwargs):
        return run(cmd, capture_output=True, text=True, timeout=120, **kwargs)

    try:
        log(f'[deploy] reading Pinky {config}')
        result = call(ssh_cmd(host, control, 'cat -- ' + shlex.quote(config)))
        if result.returncode != 0:
            return False, f'cannot read Pinky YAML: {result.stderr.strip()}'
        try:
            diffs = non_hsv_differences(result.stdout, local_text)
        except Exception as exc:  # noqa: BLE001
            return False, f'Pinky YAML unreadable: {exc}'
        if diffs:
            return False, (
                'Pinky YAML differs from laptop in non-HSV keys (not '
                'overwriting them silently): ' + ', '.join(diffs))

        log(f'[deploy] uploading to {temp}')
        result = call(scp_cmd(host, control, local_path, temp))
        if result.returncode != 0:
            return False, f'upload failed (Pinky YAML untouched): {result.stderr.strip()}'

        log(f'[deploy] backup {backup} + atomic replace')
        result = call(ssh_cmd(host, control, 'sh -s'),
                      input=replace_script(config, temp, backup, sha))
        if result.returncode != 0:
            detail = (result.stdout + result.stderr).strip().splitlines()
            return False, 'remote replace failed: ' + (detail[-1] if detail else '?')
        ok, reason = verify_remote_output(result.stdout, local_text)
        if ok:
            log(f'[deploy] Pinky backup: {backup}')
        return ok, reason
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f'ssh/scp error: {exc}'
    finally:
        try:
            run(['ssh', '-o', f'ControlPath={control}', '-O', 'exit', host],
                capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass
        shutil.rmtree(control_dir, ignore_errors=True)
