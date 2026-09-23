#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "이 파일은 실행하지 말고 source로 적용하세요:"
    echo "source ~/KSAM/NILARM/scripts/activate_pumpkin_harvest.sh"
    exit 1
fi

NILARM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OMX_VENV="$HOME/venv/omx"

if [[ "${VIRTUAL_ENV:-}" != "$OMX_VENV" ]]; then
    source "$OMX_VENV/bin/activate"
fi

# 가상환경 적용 후 ROS2 경로를 마지막에 추가해야 한다.
source /opt/ros/jazzy/setup.bash

export NILARM_REPOSITORY_ROOT="$NILARM_ROOT"
export AMENT_PREFIX_PATH="$NILARM_ROOT/install/arm_control_pkg:${AMENT_PREFIX_PATH:-}"
export PYTHONPATH="$NILARM_ROOT/src/arm_control_pkg:$NILARM_ROOT/src/vision_pkg:$NILARM_ROOT/build/arm_control_pkg:${PYTHONPATH:-}"

echo "NILARM 수확 환경 적용 완료"
echo "  저장소: $NILARM_ROOT"
echo "  Python: $(command -v python3)"
