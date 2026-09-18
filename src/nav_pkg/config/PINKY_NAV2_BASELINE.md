# Pinky Pro Nav2 baseline

This baseline follows the public Pinky Pro ROS 2 Jazzy packages and the Nav2
Jazzy bringup structure. The official robot supports lidar, but NILARM does
not use it, so all scan layers are disabled here. It is deliberately separate
from the KSAM camera road-perception pipeline.

## Assumed Pinky interfaces

- Command: `/cmd_vel`, `geometry_msgs/msg/Twist`
- Odometry: `/odom`, child frame `base_footprint`
- Robot frames: `odom -> base_footprint -> base_link`
- Lidar: not used in NILARM
- Footprint: square corners at `+/-0.06 m`, plus `0.03 m` padding
- Differential-drive controller: Regulated Pure Pursuit
- Nav2 command chain: controller/behaviors -> `cmd_vel_nav` -> velocity
  smoother -> `/cmd_vel`

## Safety boundary

The launch default is `autostart:=false`. Starting it creates inactive Nav2
lifecycle nodes and must not be treated as authorization to drive the robot.
Do not activate Nav2 until all checks below pass with the wheels safely lifted
or motor power disabled. This baseline has no obstacle detection or avoidance.

## Preflight checks

```bash
export ROS_DOMAIN_ID=99
source /opt/ros/jazzy/setup.bash
cd ~/NILARM
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select nav_pkg --symlink-install
source ~/NILARM/install/setup.bash

ros2 topic type /cmd_vel
ros2 topic type /odom
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint base_link
ros2 topic info /cmd_vel -v
```

If `nav2_bringup` is still unavailable, install the released Jazzy binaries:

```bash
sudo apt update
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
```

Expected message types are `geometry_msgs/msg/Twist` and
`nav_msgs/msg/Odometry`. No `/scan` input is configured.

## Inactive configuration inspection

```bash
ros2 launch nav_pkg pinky_nav2_base.launch.py autostart:=false
```

This is only the generic Pinky/Nav2 baseline. Its rolling costmaps contain no
sensor obstacles. The KSAM route state machine, camera-derived safety input,
rotary behavior, IMU fusion, and command ownership must be integrated later.

Never run `line_follower` while this Nav2 stack is active. Before activation,
`ros2 topic info /cmd_vel -v` must show only the Nav2 velocity smoother as a
publisher and `pinky_bringup` as the motor-side subscriber.
