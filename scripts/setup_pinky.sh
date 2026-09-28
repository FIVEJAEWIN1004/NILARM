#!/usr/bin/env bash
# One-time Pinky setup (and rebuild after updates). Not needed per match.
#   cd ~/NILARM && ./scripts/setup_pinky.sh [--no-command]
# Builds only the robot packages into .pinky_ws/ and links `nilarm` and
# `nilarm-start` into ~/.local/bin. No sudo, no ~/.bashrc edits.
set -eo pipefail

PACKAGES=(interfaces_pkg pinky_camera_drive pinky_media nilarm_bringup)
repo="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
scripts="${repo}/src/nilarm_bringup/scripts"

source "${scripts}/nilarm_env.sh" || exit 1
echo "NILARM repo: ${NILARM_REPO}  ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"

missing=0
for pkg in pinky_bringup camera_pkg rosidl_default_generators std_srvs nav_msgs; do
    if ! ros2 pkg prefix "${pkg}" >/dev/null 2>&1; then
        echo "MISSING ROS package: ${pkg}" >&2
        missing=1
    fi
done
for mod in cv2 numpy pinkylib pinky_lcd PIL; do
    if ! python3 -c "import ${mod}" 2>/dev/null; then
        echo "MISSING Python module: ${mod}" >&2
        missing=1
    fi
done
(( missing == 0 )) || { echo "Fix the missing dependencies above first." >&2; exit 1; }

if grep -qs 'LIBCAMERA_IPA_MODULE_PATH' "$HOME/.bashrc"; then
    echo "NOTE: ~/.bashrc exports custom libcamera paths globally. nilarm ignores"
    echo "      them (camera node gets them from the launch); removing them is optional."
fi

cd "${NILARM_REPO}"
colcon --log-base "${NILARM_WS}/log" build --symlink-install \
    --base-paths src \
    --build-base "${NILARM_WS}/build" --install-base "${NILARM_WS}/install" \
    --packages-select "${PACKAGES[@]}" \
    --allow-overriding pinky_camera_drive pinky_media

if [[ "$1" != "--no-command" ]]; then
    mkdir -p "$HOME/.local/bin"
    ln -sfn "${scripts}/nilarm" "$HOME/.local/bin/nilarm"
    ln -sfn "${scripts}/nilarm-start" "$HOME/.local/bin/nilarm-start"
    echo "Installed: ~/.local/bin/nilarm, ~/.local/bin/nilarm-start"
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) echo "~/.local/bin is not on PATH in this shell; open a new login shell (ssh again)." ;;
    esac
fi

cat <<'USAGE'

Ready. One time for the laptop link: ./scripts/setup_remote_harvest.sh <user>@<laptop_ip>
Every match:
  nilarm          # starts Pinky + laptop /harvest server, checks everything, then STARTs
If a check fails the robot stays stopped; fix it and run `nilarm-start`.
Do not run the laptop camera_straight_drive (exactly one drive node allowed).
USAGE
