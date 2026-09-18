"""Wire Nav2 smoother through the camera controller without cmd_vel conflict."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    vision_share = Path(get_package_share_directory('vision_pkg'))
    nav_share = Path(get_package_share_directory('nav_pkg'))
    vision_params = LaunchConfiguration('vision_params')
    nav_params = LaunchConfiguration('nav_params')
    autostart = LaunchConfiguration('autostart')

    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(nav_share / 'launch' / 'pinky_nav2_base.launch.py')),
        launch_arguments={
            'params_file': nav_params,
            'autostart': autostart,
            'final_cmd_vel_topic': 'cmd_vel_nav_smoothed',
        }.items(),
    )

    vision_node = Node(
        package='vision_pkg',
        executable='camera_drive_controller',
        name='camera_drive_controller',
        output='screen',
        parameters=[vision_params],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'nav_params',
            default_value=str(
                nav_share / 'config' / 'nav2_pinky_base.yaml')),
        DeclareLaunchArgument(
            'vision_params',
            default_value=str(
                vision_share / 'config' / 'camera_drive_controller.yaml')),
        DeclareLaunchArgument('autostart', default_value='false'),
        nav_launch,
        vision_node,
    ])
