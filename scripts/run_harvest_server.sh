#!/usr/bin/env bash
# LAPTOP side (Pinky calls this over SSH): run the OMX /harvest Action Server
# at most once, in the background, exactly as verified by hand:
#   source scripts/activate_pumpkin_harvest.sh; export ROS_DOMAIN_ID=99
#   python3 -m arm_control_pkg.pumpkin_harvest.harvest_action_server \
#     --ros-args -p harvest_all_detected:=true
# usage: run_harvest_server.sh start | check | status | build | restart
#   build:   colcon build --packages-up-to arm_control_pkg in the OMX env
#   restart: SIGTERM exactly the one running server (PID file / exact cmdline),
#            start the current code, wait until /harvest has exactly 1 server
# Log: <repo>/.nilarm_logs/harvest_server.log, PID: harvest_server.pid (git-ignored)
repo="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
log_dir="${repo}/.nilarm_logs"
log="${log_dir}/harvest_server.log"
pid_file="${log_dir}/harvest_server.pid"
domain="${ROS_DOMAIN_ID:-99}"

server_pids() {
    pgrep -f -- 'pumpkin_harvest\.harvest_action_server|/harvest_action_server( |$)'
}

use_desktop_display() {
    # The scan shows an OpenCV (Qt/xcb) window; with no X display Qt aborts the
    # whole server mid-harvest. Attach to the logged-in desktop session.
    [[ -n "${DISPLAY}" ]] && return 0
    local sock auth
    sock="$(ls /tmp/.X11-unix/ 2>/dev/null | head -1)"
    auth="$(ls "/run/user/$(id -u)"/.mutter-Xwaylandauth.* 2>/dev/null | head -1)"
    [[ -z "${auth}" && -f "$HOME/.Xauthority" ]] && auth="$HOME/.Xauthority"
    [[ -n "${sock}" && -n "${auth}" ]] || return 1
    export DISPLAY=":${sock#X}" XAUTHORITY="${auth}"
}

in_harvest_env() {  # run "$@" inside the verified OMX/ROS environment
    (cd "${repo}" && source scripts/activate_pumpkin_harvest.sh >/dev/null \
        && export ROS_DOMAIN_ID="${domain}" && "$@")
}

start_server() {
    if pids="$(server_pids)"; then
        echo "harvest server already running (pid ${pids//$'\n'/ }); not starting another"
        return 0
    fi
    use_desktop_display || {
        echo "FAIL: no desktop X display for the OpenCV scan window; log in on the laptop"
        return 1
    }
    echo "=== $(date '+%F %T') start (DISPLAY=${DISPLAY}, ROS_DOMAIN_ID=${domain})" >>"${log}"
    # 9>&- : the long-running server must not keep holding the start lock.
    setsid nohup bash -c 'cd "$1" && source scripts/activate_pumpkin_harvest.sh \
        && export ROS_DOMAIN_ID="$2" \
        && exec python3 -m arm_control_pkg.pumpkin_harvest.harvest_action_server \
           --ros-args -p harvest_all_detected:=true' _ "${repo}" "${domain}" \
        >>"${log}" 2>&1 </dev/null 9>&- &
    pid=$!
    echo "${pid}" >"${pid_file}"
    sleep "${NILARM_HARVEST_SETTLE_SEC:-5}"
    if ! kill -0 "${pid}" 2>/dev/null; then
        echo "FAIL: harvest server exited during startup; last log lines:"
        tail -n 20 "${log}"
        return 1
    fi
    echo "harvest server started (pid ${pid}, log ${log})"
}

stop_server() {  # SIGTERM only the one verified server pid, never a pattern kill
    local pids pid count _
    pids="$(server_pids)" || { echo "no harvest server running"; return 0; }
    count="$(wc -l <<<"${pids}")"
    if (( count > 1 )); then
        echo "FAIL: ${count} harvest servers running (pid ${pids//$'\n'/ }); stop them by hand first"
        return 1
    fi
    pid="$(cat "${pid_file}" 2>/dev/null)"
    if [[ "${pid}" == "${pids}" ]]; then
        echo "stopping harvest server pid ${pid} (PID file verified)"
    else
        pid="${pids}"
        echo "stopping harvest server pid ${pid} (PID file missing/stale; exact cmdline match)"
    fi
    kill -TERM "${pid}" || { echo "FAIL: cannot signal harvest server pid ${pid}"; return 1; }
    for _ in $(seq 1 $(( ${NILARM_HARVEST_STOP_SEC:-15} * 10 ))); do
        kill -0 "${pid}" 2>/dev/null || { rm -f "${pid_file}"; echo "stopped pid ${pid}"; return 0; }
        sleep 0.1
    done
    echo "FAIL: harvest server pid ${pid} did not exit after SIGTERM; not starting another"
    return 1
}

wait_harvest_ready() {  # exactly one /harvest server on the ROS graph
    local servers deadline=$(( SECONDS + ${NILARM_HARVEST_READY_SEC:-30} ))
    while :; do
        servers="$(in_harvest_env timeout 10 ros2 action info /harvest 2>/dev/null \
            | awk '/^Action servers:/ {print $NF; exit}')"
        [[ "${servers}" == 1 ]] && { echo "OK: /harvest ready (1 server)"; return 0; }
        (( SECONDS >= deadline )) && break
        sleep 1
    done
    echo "FAIL: /harvest not ready (servers=${servers:-0}, need 1); log ${log}"
    return 1
}

case "${1:-start}" in
status)
    pids="$(server_pids)" && echo "running: ${pids//$'\n'/ }" || { echo "not running"; exit 1; }
    ;;
check)
    in_harvest_env python3 -c \
        'import arm_control_pkg.pumpkin_harvest.harvest_action_server, interfaces_pkg.action' \
        || { echo "FAIL: harvest server does not import in the OMX env"; exit 1; }
    echo "OK: OMX env + harvest_action_server import"
    use_desktop_display || { echo "FAIL: no desktop X display (log in on the laptop)"; exit 1; }
    in_harvest_env python3 -c 'import cv2, numpy
cv2.imshow("nilarm check", numpy.zeros((8, 8, 3), "uint8")); cv2.waitKey(1)
cv2.destroyAllWindows()' || { echo "FAIL: OpenCV window cannot open on ${DISPLAY}"; exit 1; }
    echo "OK: OpenCV window on ${DISPLAY}"
    ;;
start)
    mkdir -p "${log_dir}"
    exec 9>"${log_dir}/harvest_server.lock"
    flock -w 20 9 || { echo "FAIL: another start is still in progress"; exit 1; }
    start_server || exit 1
    ;;
build)
    [[ -f "$HOME/venv/omx/bin/activate" ]] || { echo "FAIL: OMX venv missing ($HOME/venv/omx)"; exit 1; }
    cd "${repo}" || exit 1
    source scripts/activate_pumpkin_harvest.sh || { echo "FAIL: OMX/ROS env (scripts/activate_pumpkin_harvest.sh)"; exit 1; }
    export ROS_DOMAIN_ID="${domain}"
    colcon build --packages-up-to arm_control_pkg --symlink-install \
        || { echo "FAIL: colcon build arm_control_pkg"; exit 1; }
    source install/setup.bash || exit 1
    echo "OK: arm_control_pkg built (${repo})"
    ;;
restart)
    mkdir -p "${log_dir}"
    exec 9>"${log_dir}/harvest_server.lock"
    flock -w 20 9 || { echo "FAIL: another start is still in progress"; exit 1; }
    stop_server || exit 1
    start_server || exit 1
    wait_harvest_ready || exit 1
    echo "log: ${log}"
    ;;
*)
    echo "usage: $0 start|check|status|build|restart" >&2
    exit 2
    ;;
esac
