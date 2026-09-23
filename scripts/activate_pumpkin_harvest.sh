#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "이 파일은 실행하지 말고 source로 적용하세요:"
    echo "source ~/KSAM/NILARM/scripts/activate_pumpkin_harvest.sh"
    exit 1
fi

NILARM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source /opt/ros/jazzy/setup.bash
source "$HOME/venv/omx/bin/activate"

export NILARM_REPOSITORY_ROOT="$NILARM_ROOT"
export AMENT_PREFIX_PATH="$NILARM_ROOT/install/arm_control_pkg:${AMENT_PREFIX_PATH:-}"
export PYTHONPATH="$NILARM_ROOT/src/arm_control_pkg:${PYTHONPATH:-}"

echo "NILARM 수확 환경 적용 완료"
echo "  저장소: $NILARM_ROOT"
echo "  Python: $(command -v python3)"
