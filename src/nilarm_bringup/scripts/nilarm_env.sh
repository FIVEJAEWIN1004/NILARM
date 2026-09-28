# Sourced by nilarm / nilarm-start / scripts/*_pinky.sh. Pinky ROS environment:
#   /opt/ros/jazzy -> ~/camera_ws -> ~/pinky_pro -> NILARM (.pinky_ws overlay)
# The Pi build lives in .pinky_ws/, not the repo's tracked build/ install/.

NILARM_REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../.." && pwd)"
NILARM_WS="${NILARM_REPO}/.pinky_ws"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-99}"

# ~/.bashrc may export the custom libcamera paths globally; keep them out of
# motor/drive/LED/LCD. competition.launch.py hands them to the camera only.
unset LIBCAMERA_IPA_MODULE_PATH LD_LIBRARY_PATH

for underlay in /opt/ros/jazzy "$HOME/camera_ws/install" "$HOME/pinky_pro/install"; do
    if [[ ! -f "${underlay}/setup.bash" ]]; then
        echo "nilarm: missing ${underlay}/setup.bash" >&2
        return 1
    fi
    source "${underlay}/setup.bash"
done
if [[ -f "${NILARM_WS}/install/setup.bash" ]]; then
    source "${NILARM_WS}/install/setup.bash"
fi
