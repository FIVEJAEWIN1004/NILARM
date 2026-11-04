# NILARM — 프로젝트 안내 (Codex/에이전트용)

KSAM 대회용 **호박 수확 로봇** (ROS 2 Jazzy).
- **Pinky** (Raspberry Pi 모바일 로봇): 노란 경계선을 카메라로 따라 주행 → 수확 지점에 정지 → 수확 요청 → 다음 지점 → 골인.
- **노트북 + OMX 로봇팔**: `/harvest` Action Server. 팔 카메라 + YOLO로 호박을 스캔하고, 주황(익은) 호박만 집어 바구니에 넣음.
- 두 기기는 같은 Wi-Fi, `ROS_DOMAIN_ID=99` 로 통신. Pinky가 SSH로 노트북의 수확 서버를 원격 실행.

## 대회 실행 흐름

```
[Pinky] nilarm
  ├─ ros2 launch nilarm_bringup competition.launch.py
  │    pinky_bringup(모터/odom) · camera_pkg camera_publisher · pinky_status_display(LED/LCD)
  │    · camera_straight_drive (DISABLED 상태로 시작, 하나라도 죽으면 전체 종료)
  └─ nilarm-start (사이드카)
       1) scripts/start_remote_harvest.sh → SSH → [노트북] scripts/run_harvest_server.sh start
       2) 준비 확인: drive 노드 1개, /camera_drive/enable, /camera/image/compressed, /odom, /harvest 서버 1개
       3) 모두 OK이면 /harvest/prescan 요청(백그라운드, 실패해도 출발엔 영향 없음)
          → 노트북 OMX가 Pinky 주행 중에 스캔하고, 스캔이 끝나면 중앙 자세로 대기
       4) /camera_drive/enable true → 주행 시작 (준비 확인이 하나라도 실패하면 정지 유지)
  STATION 도착 → /harvest goal → 대기 중인 pre-scan 결과로 바로 수확 (없거나 실패/만료면 기존 스캔→수확)
```

주행 상태머신 (`camera_straight_drive.py`, 현재 config 기준 `waypoint_station_mode: true`):
`DISABLED → CAMERA_DRIVING(노란선 추종 0.84m) → CURVE_TO_FIRST_POINT → FIRST_POINT_REACHED → STATION_WAIT → STATION_TO_WAYPOINT → STATION_MOVE → STATION_REACHED → STATION_LOAD_WAIT(/harvest goal 전송, 결과 대기) → STATION_TO_NEXT_STOP → NEXT_STOP_FINAL_ROTATE → NEXT_WAYPOINT_WAIT/MOVE → FINAL_CAMERA_DRIVING(0.60m) → FINAL_STRAIGHT_DRIVING(0.33m) → FINAL_REACHED`. 이상 시 `FAULT`. 이름이 `*_TEST_*`인 상태는 config의 테스트 모드 플래그로만 진입.

## ROS 인터페이스 (실제로 쓰이는 것)

| 이름 | 타입 | 발행/제공 → 사용 |
|---|---|---|
| `/camera/image/compressed` | sensor_msgs/CompressedImage | camera_pkg → drive, HSV 캘리브레이터 |
| `/odom` | nav_msgs/Odometry | pinky_bringup → drive |
| `/cmd_vel` | geometry_msgs/Twist | drive → pinky_bringup (status_display도 구독) |
| `/camera_drive/enable` | std_srvs/SetBool (service) | nilarm-start → drive |
| `/camera_drive/state` | std_msgs/String | drive → (모니터링) |
| `/harvest` | interfaces_pkg/action/Harvest | 노트북 harvest_action_server ← drive(client) |
| `/harvest/prescan` | std_srvs/Trigger (service) | nilarm-start → 노트북 harvest server (`prescan.py`) |
| `/harvest/display_result` | String (TRANSIENT_LOCAL) | harvest server → status_display (예: `A-N / B-N`) |
| `/pinky/display_mode` | String (`IMAGE` 등) | drive → status_display |
| `/pinky/music_control` | String (`START`/`STOP`) | drive → music_player / buzzer_player |

`Harvest.action`: goal `target_count` / result `success, harvested_count` / feedback `current_count, status`.
`interfaces_pkg`의 나머지(DumpBasket, NavigationGoal, *.msg)는 정의만 있고 현재 대회 흐름에서는 안 씀.

## 패키지별 역할 (`src/`)

### `nilarm_bringup` — 대회 진입점 (Pinky)
- `launch/competition.launch.py` — 대회 때 Pinky에서 도는 노드 전부. 커스텀 libcamera 경로(`/usr/local/lib/aarch64-linux-gnu`)는 카메라 프로세스에만 줌.
- `scripts/nilarm` — 단 하나의 대회 명령. `NILARM_AUTO_START=0`이면 launch만 실행.
- `scripts/nilarm-start` — 안전 게이트 + enable. 수동으로 재시도/디버그할 때도 사용.
- `scripts/nilarm_env.sh` — 환경 소싱: `/opt/ros/jazzy → ~/camera_ws → ~/pinky_pro → NILARM/.pinky_ws`.
- `test/test_nilarm_start.py` — `ros2`/`ssh` 스텁으로 게이트 로직 테스트.

### `pinky_camera_drive` — 주행 (Pinky)
- `camera_straight_drive.py` (~2600줄) — 핵심 노드. 노란 경계선 HSV 검출 + 직선 피팅으로 조향, odom 기반 거리/베지어 곡선 이동, `/harvest` Action client, LCD/음악 신호.
- `config/camera_straight_drive.yaml` — 속도, 거리, 곡선/웨이포인트 목표 좌표, ROI, `yellow_*` HSV 임계값, 적응형 S/V 보정. **현장 튜닝은 거의 여기서 함.**
- `hsv_calibrator.py` — (노트북) Pinky 카메라를 구독만 하면서 노란선을 클릭해 `yellow_*` 6개 키 갱신. publish 안 함 → 로봇 안 움직임.
- `hsv_deploy.py` — 캘리브레이션된 YAML만 Pinky로 scp (백업·체크섬·검증). 기본 주소 `DEFAULT_PINKY_HOST`.
- `hsv_utils.py` — ROS 없는 순수 HSV 계산 (테스트 대상).

### `pinky_media` — LED/LCD/음악 (Pinky)
- `pinky_status_display.py` — `/cmd_vel`, `/harvest/display_result`, `/pinky/display_mode`를 보고 LED/LCD 표시 (`pinkylib`, `pinky_lcd` 필요).
- `music_player.py` (mp3), `buzzer_player.py` + `keroro_buzzer_melody.py` (부저 멜로디). `assets/`에 이미지·음악.

### `arm_control_pkg` — OMX 팔 수확 (노트북)
`pumpkin_harvest/`가 실제 코드:
- `harvest_action_server.py` — `/harvest` 서버. goal 수락 후에야 OMX/YOLO 스택을 import해서 `v5.run_harvest()` 호출. 파라미터 `harvest_all_detected` (대회에선 `true`: 감지된 익은 호박 전부 수확해야 성공).
- `prescan.py` — pre-scan 조정기. `run_harvest`를 별도 스레드에서 돌리다가 스캔과 수확 사이(`before_harvest` 훅)에서 /harvest goal을 기다림. 결과는 한 번만 사용, 미사용 시 `prescan_ready_timeout_sec`(기본 180초) 후 만료, OMX 사용은 lock으로 하나만.
- `fake_harvest_action_server.py` — 하드웨어 없는 테스트용 서버 (`ros2 run arm_control_pkg fake_harvest_server`).
- 수확 파이프라인 (import 체인): `..._to_bin_v5.py`(대회 출력 `A-N / B-N`, +Y=A/−Y=B) → `v4`(팔 속도 1.5배) → `v2`(바구니까지 전체 자동) → `pumpkin_auto_scan_count_orange_harvest.py`(joint1 전체 스캔·개수 세기·주황 분류) → `pumpkin_detected_approach_validation.py`, `pumpkin_multiangle_approach_validation.py`, `pumpkin_orange_auto_grasp_validation.py`(접근·파지 공통 로직).
- `arm_camera.py` — OMX 팔 카메라(Innomaker)를 `/dev/videoN` 번호가 아니라 V4L2 이름/capability로 찾음. **노트북 내장 카메라로 절대 fallback 하지 않음.**
- `runtime_paths.py` — YOLO 모델(`src/vision_pkg/models/nil_pumpkin.pt` 등) 경로 탐색.
- `*.json` — 캘리브레이션 결과(픽셀→팔 평면 9점, 각도별 XY 잔차, 파지 자세, 바구니 자세). 실물 측정값이니 손으로 바꾸지 말 것.
- `tools/` — 위 json을 만드는 캘리브레이션/티칭/검증 스크립트.
- 패키지 루트의 `arm_controller.py`, `harvesting_node.py`, `target_receiver.py`, `gripper_controller.py`는 초기 버전 (현재 흐름에서 안 씀).
- `test/` — 대부분 실험용 수동 스크립트 (`test/30/` 포함). 자동 테스트는 `test_arm_camera.py` 정도.

### `vision_pkg` — 모델 + 검출 라이브러리
- 현재 쓰이는 것: `vision_pkg/pumpkin_detection/` (`yolo_detector`, `color_classifier`(HSV 주황/초록), `spatial_tracking`(중복 제거)) 와 `models/*.pt`. arm 수확 코드가 import.
- `camera_drive_controller.py`, `straight_nav_controller.py`, `rpicam_publisher.py`, `vision_node.py`, `hsv_detector.py`, `launch/`, `config/` 는 이전 주행 방식의 레거시 (대회 launch에 없음).

### `interfaces_pkg` — 메시지/액션 정의 (CMake). 위 표 참고.

## `scripts/` (repo 루트)

| 스크립트 | 실행 위치 | 역할 |
|---|---|---|
| `setup_pinky.sh` | Pinky, 1회/업데이트 후 | 의존성 검사, 4개 패키지만 `.pinky_ws/`에 빌드, `nilarm`·`nilarm-start`를 `~/.local/bin`에 링크 |
| `update_pinky.sh` | Pinky | 로컬 변경 없을 때만 `git pull --ff-only` + 재빌드 |
| `setup_remote_harvest.sh <user>@<host>` | Pinky, 1회 | 노트북 SSH 키 설정, 주소를 `.nilarm_remote_env`에 저장 |
| `start_remote_harvest.sh` | Pinky | `/harvest` 서버가 없으면 SSH로 노트북에서 시작 |
| `run_harvest_server.sh start\|check\|status` | 노트북 | 수확 서버를 1개만 백그라운드 실행 (OpenCV 창 때문에 데스크톱 DISPLAY 연결). 로그 `.nilarm_logs/harvest_server.log` |
| `activate_pumpkin_harvest.sh` | 노트북 (`source`) | `~/venv/omx` + ROS + install 환경 적용 |
| `ksam_hsv_calibrate` | 노트북 | HSV 캘리브레이터 실행 후 YAML을 Pinky로 배포 (`--no-deploy` 가능) |
| `start_remote_hsv_calibrate.sh` | Pinky | Pinky에서 `ksam_hsv_calibrate` 입력 시: 카메라만 켜고 노트북 캘리브레이터를 SSH로 띄움 |

`tools/run_pinky_course.sh` — 예전 코스 실행 스크립트 (git 미추적).

## 빌드 / 테스트

```bash
# 노트북 (전체)
source /opt/ros/jazzy/setup.bash && colcon build --symlink-install
# Pinky
./scripts/setup_pinky.sh

# 테스트 (ROS + install 소싱 후, 디렉터리별 실행 — 현재 84개 전부 통과)
source /opt/ros/jazzy/setup.bash && source install/setup.bash
python3 -m pytest -q src/nilarm_bringup/test
python3 -m pytest -q src/pinky_camera_drive/test
python3 -m pytest -q src/pinky_media/test
python3 -m pytest -q src/arm_control_pkg/test/test_arm_camera.py
```

## 환경 / 로컬 파일 (git-ignored)
- `.pinky_ws/` — Pinky 빌드 결과 (repo의 `build/ install/`과 별개).
- `.nilarm_remote_env` — 노트북 주소/사용자 (Pinky). `.nilarm_pinky_env` — Pinky 주소 (노트북).
- `.nilarm_logs/` — 노트북 수확 서버 로그.
- 노트북 의존성: `~/venv/omx` (ultralytics, `omx_f` OMX 드라이버). Pinky 의존성: `pinky_bringup`, `camera_pkg`, `pinkylib`, `pinky_lcd`.

## 작업 시 주의
- **안전 우선**: drive 노드는 DISABLED로 시작하고 `/camera_drive/enable` 전엔 zero Twist만 냄. 게이트 조건을 약화시키지 말 것.
- 실물 하드웨어/캘리브레이션 값(yaml 튜닝값, `pumpkin_harvest/*.json`)은 현장 측정 결과임. 이유 없이 바꾸지 말 것.
- `*.bak*` 파일은 수정 전 백업본 (git 미추적). 참고만 하고 편집 대상 아님.
- `archive/` (`COLCON_IGNORE`) — 예전 `drive_pkg`, `nav_pkg`(Nav2/IR 정렬/라인 추종). 빌드 안 됨. (`archive/vision_pkg`는 `src/vision_pkg` 사본이라 git 미추적.)
