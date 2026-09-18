"""Launch the inactive-by-default Pinky IR final-alignment node."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory('nav_pkg'))
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=str(package_share / 'config' / 'ir_align_params.yaml'),
        ),
        Node(
            package='nav_pkg',
            executable='ir_align_node',
            name='ir_align_node',
            output='screen',
            parameters=[LaunchConfiguration('params_file')],
        ),
    ])
