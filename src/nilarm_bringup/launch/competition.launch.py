"""Everything Pinky runs in a match. The robot stays DISABLED until
/camera_drive/enable true (nilarm-start); the /harvest server runs on the laptop.
"""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node

# Custom libcamera 0.3.2 (OV5647) lives in /usr/local; only the camera process
# gets it, so motor/drive/LED/LCD keep the stock ROS library path.
CAMERA_LIB = '/usr/local/lib/aarch64-linux-gnu'


def generate_launch_description():
    camera_env = {
        'LD_LIBRARY_PATH': ':'.join(filter(None, [
            CAMERA_LIB,
            '/opt/ros/jazzy/lib',
            '/opt/ros/jazzy/lib/aarch64-linux-gnu',
            os.environ.get('LD_LIBRARY_PATH', ''),
        ])),
        'LIBCAMERA_IPA_MODULE_PATH': CAMERA_LIB + '/libcamera',
    }
    drive_params = str(
        Path(get_package_share_directory('pinky_camera_drive'))
        / 'config' / 'camera_straight_drive.yaml')

    bringup = Node(
        package='pinky_bringup', executable='bringup', name='pinky_bringup',
        output='screen', emulate_tty=True)
    camera = Node(
        package='camera_pkg', executable='camera_publisher',
        name='camera_publisher', output='screen', emulate_tty=True,
        additional_env=camera_env)
    status_display = Node(
        package='pinky_media', executable='pinky_status_display',
        name='pinky_status_display', output='screen', emulate_tty=True)
    # Starts DISABLED (zero Twist); only /camera_drive/enable true moves it.
    drive = Node(
        package='pinky_camera_drive', executable='camera_straight_drive',
        name='camera_straight_drive', output='screen', emulate_tty=True,
        parameters=[drive_params])

    # Losing motors, camera or the driver must not leave a half-running robot.
    stop_on_exit = [
        RegisterEventHandler(OnProcessExit(
            target_action=action,
            on_exit=[EmitEvent(event=Shutdown(reason=f'{name} exited'))]))
        for action, name in ((bringup, 'pinky_bringup'),
                             (camera, 'camera_publisher'),
                             (drive, 'camera_straight_drive'))]

    return LaunchDescription(
        [bringup, camera, status_display, drive] + stop_on_exit)
