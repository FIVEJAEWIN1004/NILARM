"""Launch the disabled-by-default Pinky camera straight-drive test node."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('pinky_camera_drive'))
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=str(
                share / 'config' / 'camera_straight_drive.yaml')),
        Node(
            package='pinky_camera_drive',
            executable='camera_straight_drive',
            name='camera_straight_drive',
            output='screen',
            parameters=[LaunchConfiguration('params_file')],
        ),
    ])
