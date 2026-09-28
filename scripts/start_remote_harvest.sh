#!/usr/bin/env bash
# PINKY side: make sure the laptop /harvest Action Server is running.
#   exit 0 = already on the ROS graph, already running, or just started
#   exit 1 = SSH/start failed; exit 2 = laptop not configured
# Never prompts: key auth only (BatchMode), host key must already be known.
# Laptop address/user come from <repo>/.nilarm_remote_env (git-ignored) or
# the environment; see scripts/setup_remote_harvest.sh.
repo="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
if ! command -v ros2 >/dev/null; then
    source "${repo}/src/nilarm_bringup/scripts/nilarm_env.sh" || exit 1
fi
if [[ -z "${NILARM_LAPTOP_HOST}" && -f "${repo}/.nilarm_remote_env" ]]; then
    source "${repo}/.nilarm_remote_env"
fi

servers="$(timeout 10 ros2 action info /harvest 2>/dev/null \
    | awk '/^Action servers:/ {print $NF; exit}')"
if (( ${servers:-0} >= 1 )); then
    echo "remote-harvest: /harvest server already on the ROS graph (${servers}); not starting"
    exit 0
fi

if [[ -z "${NILARM_LAPTOP_HOST}" || -z "${NILARM_LAPTOP_USER}" ]]; then
    echo "remote-harvest: laptop not configured (run scripts/setup_remote_harvest.sh)" >&2
    exit 2
fi
key="${NILARM_SSH_KEY:-$HOME/.ssh/nilarm_laptop_ed25519}"
ssh_opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes
          -o ConnectTimeout="${NILARM_SSH_TIMEOUT:-5}"
          -o ServerAliveInterval=5 -o ServerAliveCountMax=2)
[[ -f "${key}" ]] && ssh_opts+=(-i "${key}" -o IdentitiesOnly=yes)

echo "remote-harvest: no /harvest yet; asking ${NILARM_LAPTOP_USER}@${NILARM_LAPTOP_HOST}"
timeout 40 ssh "${ssh_opts[@]}" "${NILARM_LAPTOP_USER}@${NILARM_LAPTOP_HOST}" \
    "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-99} bash \"\$HOME/${NILARM_LAPTOP_REPO:-NILARM}/scripts/run_harvest_server.sh\" start"
rc=$?
if (( rc != 0 )); then
    echo "remote-harvest: FAILED (rc=${rc}: SSH/Wi-Fi/key/laptop/server problem)" >&2
    exit 1
fi
