#!/usr/bin/env bash
# PINKY: `ksam_hsv_calibrate` (linked by scripts/setup_pinky.sh). Makes sure
# the Pinky camera publishes, then opens the HSV calibrator on the LAPTOP
# desktop over SSH. The only thing ever started here is camera_pkg
# camera_publisher (no motors, drive, bringup, nilarm or /cmd_vel), and only
# when no camera is running; that camera is stopped again on exit/Ctrl+C.
# After ENTER the laptop copies the calibrated YAML back here and verifies it;
# its result banner prints below.
#   ksam_hsv_calibrate [laptop calibrator options, e.g. --no-deploy]
# Laptop address: same as remote harvest -> <repo>/.nilarm_remote_env or the
# environment (scripts/setup_remote_harvest.sh). Key auth only (BatchMode).
# exit: calibrator's code (0 done, 1 cancelled, 2/3 no camera, 4 deploy failed),
#       10 laptop DISPLAY unavailable, 11 already running,
#       20 laptop not configured, 21 laptop unreachable,
#       22 camera failed to start, 23 camera process running but no frames
repo="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
if [[ -z "${NILARM_LAPTOP_HOST}" && -f "${repo}/.nilarm_remote_env" ]]; then
    source "${repo}/.nilarm_remote_env"
fi
if [[ -z "${NILARM_LAPTOP_HOST}" || -z "${NILARM_LAPTOP_USER}" ]]; then
    echo "HSV calibration NOT started: laptop not configured" \
         "(run scripts/setup_remote_harvest.sh <user>@<laptop_ip>)" >&2
    exit 20
fi
target="${NILARM_LAPTOP_USER}@${NILARM_LAPTOP_HOST}"

key="${NILARM_SSH_KEY:-$HOME/.ssh/nilarm_laptop_ed25519}"
ssh_opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes
          -o ConnectTimeout="${NILARM_SSH_TIMEOUT:-5}"
          -o ServerAliveInterval=5 -o ServerAliveCountMax=2 -o ForwardX11=no)
[[ -f "${key}" ]] && ssh_opts+=(-i "${key}" -o IdentitiesOnly=yes)
# A tty lets Ctrl+C here cancel the laptop calibrator and lets the laptop ask
# for the Pinky password during deploy if it has no key for Pinky.
if [[ -t 0 && -t 1 ]]; then ssh_opts+=(-t); else ssh_opts+=(-T); fi

source "${NILARM_ENV_SCRIPT:-${repo}/src/nilarm_bringup/scripts/nilarm_env.sh}" || exit 1

topic=/camera/image/compressed
# Same camera-only library environment as competition.launch.py (CAMERA_LIB,
# camera_env); applied to the camera process alone, never to this shell.
CAMERA_LIB=/usr/local/lib/aarch64-linux-gnu
camera_log_dir="$HOME/.nilarm_logs"
camera_pid=""

fresh_frame() {  # one real message within $1 s (a graph entry is not enough)
    timeout --foreground "$1" ros2 topic echo --once --qos-reliability best_effort \
        --field format "${topic}" sensor_msgs/msg/CompressedImage >/dev/null 2>&1
}
alive() {  # pid exists and is not a zombie
    local state
    state="$(ps -o stat= -p "$1" 2>/dev/null)" && [[ "${state}" != Z* ]]
}
stop_own_camera() {  # only the process group this invocation started
    [[ -n "${camera_pid}" ]] || return 0
    local pid="${camera_pid}" sig _
    camera_pid=""
    echo "HSV calibration: stopping the Pinky camera started for calibration (pid ${pid})"
    for sig in INT TERM KILL; do
        alive "${pid}" || break
        kill -s "${sig}" -- "-${pid}" 2>/dev/null
        for _ in $(seq 1 30); do alive "${pid}" || break; sleep 0.1; done
    done
    wait "${pid}" 2>/dev/null
}
trap stop_own_camera EXIT
trap 'exit 130' INT TERM HUP

echo "HSV calibration: checking Pinky camera..."
if fresh_frame "${NILARM_HSV_CAMERA_PROBE_SEC:-5}"; then
    echo "HSV calibration: Pinky camera already running"
else
    if pids="$(pgrep -f -- 'camera_pkg/camera_publisher')"; then
        echo "HSV calibration NOT started: a Pinky camera process is running" \
             "(pid ${pids//$'\n'/ }) but no frames arrive on ${topic};" \
             "not starting a duplicate. Stop/fix it (nilarm?) and retry." >&2
        exit 23
    fi
    echo "HSV calibration: starting Pinky camera..."
    mkdir -p "${camera_log_dir}"
    echo "=== $(date '+%F %T') ksam_hsv_calibrate camera start" >>"${camera_log_dir}/hsv_camera.log"
    # setsid: own process group (exact cleanup; terminal Ctrl+C reaches only
    # us). --default-signal=INT: background jobs inherit SIGINT ignored.
    setsid env --default-signal=INT \
        LD_LIBRARY_PATH="${CAMERA_LIB}:/opt/ros/jazzy/lib:/opt/ros/jazzy/lib/aarch64-linux-gnu${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}" \
        LIBCAMERA_IPA_MODULE_PATH="${CAMERA_LIB}/libcamera" \
        ros2 run camera_pkg camera_publisher \
        >>"${camera_log_dir}/hsv_camera.log" 2>&1 </dev/null &
    camera_pid=$!
    echo "HSV calibration: waiting for ${topic}..."
    deadline=$(( SECONDS + ${NILARM_HSV_CAMERA_TIMEOUT:-15} ))
    until fresh_frame "${NILARM_HSV_CAMERA_PROBE_SEC:-5}"; do
        if ! alive "${camera_pid}" || (( SECONDS >= deadline )); then
            echo "HSV calibration NOT started: Pinky camera failed to start" >&2
            echo "  log: ${camera_log_dir}/hsv_camera.log" >&2
            exit 22
        fi
    done
    echo "HSV calibration: Pinky camera ready (pid ${camera_pid}; stopped again when calibration ends)"
fi

remote="ROS_DOMAIN_ID=$(printf '%q' "${ROS_DOMAIN_ID:-99}")"
remote+=" bash \"\$HOME/${NILARM_LAPTOP_REPO:-NILARM}/scripts/ksam_hsv_calibrate\""
for arg in "$@"; do
    remote+=" $(printf '%q' "${arg}")"
done

echo "HSV calibration: opening on laptop ${target} - use the laptop screen"
ssh "${ssh_opts[@]}" "${target}" "${remote}"
rc=$?
if (( rc == 255 )); then
    echo "HSV calibration NOT started: cannot reach laptop ${target}" \
         "(Wi-Fi/SSH/key; check: scripts/setup_remote_harvest.sh)" >&2
    exit 21
fi
exit "${rc}"
