"""Safe, odometry-frame Nav2 entry point for NILARM."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    nav2_share = Path(get_package_share_directory('nav2_bringup'))
    package_share = Path(get_package_share_directory('nav_pkg'))

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(nav2_share / 'launch' / 'navigation_launch.py')
        ),
        launch_arguments={
            'params_file': LaunchConfiguration('params_file'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=str(package_share / 'config' / 'nav2_pinky_base.yaml'),
            description='No-lidar Pinky Pro odometry-frame baseline',
        ),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'autostart',
            default_value='false',
            description='Keep false until topics, TF, footprint and cmd_vel type are verified',
        ),
        navigation,
    ])
