#!/usr/bin/env bash
set -Eeo pipefail

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-99}"
source /opt/ros/jazzy/setup.bash
source /home/fivejaewin/NILARM/install/setup.bash
set -u

launch_pid=""
cleanup() {
    trap - INT TERM EXIT
    if [[ -n "${launch_pid}" ]] && kill -0 "${launch_pid}" 2>/dev/null; then
        ros2 service call /camera_drive/enable std_srvs/srv/SetBool \
            "{data: false}" >/dev/null 2>&1 || true
        kill -INT "${launch_pid}" 2>/dev/null || true
        wait "${launch_pid}" 2>/dev/null || true
    fi
}
trap cleanup INT TERM EXIT

ros2 launch pinky_camera_drive camera_straight_drive.launch.py &
launch_pid=$!

echo "주행 노드와 센서 연결을 확인합니다..."
for _ in $(seq 1 30); do
    if ros2 service list 2>/dev/null | grep -qx '/camera_drive/enable'; then
        break
    fi
    if ! kill -0 "${launch_pid}" 2>/dev/null; then
        echo "오류: camera_straight_drive launch가 종료되었습니다." >&2
        exit 1
    fi
    sleep 0.5
done

if ! ros2 service list 2>/dev/null | grep -qx '/camera_drive/enable'; then
    echo "오류: /camera_drive/enable 서비스를 찾지 못했습니다." >&2
    exit 1
fi

if ! timeout 3 ros2 topic echo /odom --once >/dev/null 2>&1; then
    echo "오류: 최신 /odom을 받지 못했습니다. 출발하지 않습니다." >&2
    exit 1
fi

if ! timeout 3 ros2 topic echo /camera/image/compressed --once \
        --field header >/dev/null 2>&1; then
    echo "오류: 카메라 프레임을 받지 못했습니다. 출발하지 않습니다." >&2
    exit 1
fi

echo
echo "센서 준비 완료: 노란 경계가 인식되면 자동으로 출발합니다."
echo "로봇 주변을 비우세요. 취소/긴급 정지는 Ctrl+C입니다."

last_notice=${SECONDS}
while true; do
    if ! kill -0 "${launch_pid}" 2>/dev/null; then
        echo "오류: 출발 전에 camera_straight_drive가 종료되었습니다." >&2
        exit 1
    fi

    response="$(timeout 3 ros2 service call /camera_drive/enable \
        std_srvs/srv/SetBool "{data: true}" 2>&1 || true)"
    if grep -q 'success=True' <<<"${response}"; then
        printf '%s\n' "${response}"
        break
    fi

    if (( SECONDS - last_notice >= 5 )); then
        echo "길 인식 대기 중: 아직 출발 조건이 충족되지 않았습니다."
        last_notice=${SECONDS}
    fi
    sleep 0.5
done

echo "주행을 시작했습니다. 긴급 정지는 이 터미널에서 Ctrl+C를 누르세요."
wait "${launch_pid}"
