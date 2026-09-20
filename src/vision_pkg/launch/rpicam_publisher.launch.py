"""Launch the OV5647 rpicam subprocess publisher."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('vision_pkg'))
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=str(share / 'config' / 'rpicam_publisher.yaml')),
        Node(
            package='vision_pkg',
            executable='rpicam_publisher',
            name='rpicam_publisher',
            output='screen',
            parameters=[LaunchConfiguration('params_file')],
        ),
    ])
