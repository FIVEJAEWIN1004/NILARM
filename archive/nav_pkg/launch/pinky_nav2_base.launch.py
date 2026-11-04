"""Inactive-by-default Nav2 baseline matching Pinky Pro interfaces."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory('nav_pkg'))
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    final_cmd_vel_topic = LaunchConfiguration('final_cmd_vel_topic')
    common_parameters = [params_file, {'use_sim_time': use_sim_time}]
    tf_remappings = [('/tf', 'tf'), ('/tf_static', 'tf_static')]
    lifecycle_nodes = [
        'controller_server', 'smoother_server', 'planner_server',
        'behavior_server', 'bt_navigator', 'waypoint_follower',
        'velocity_smoother',
    ]

    nodes = [
        Node(
            package='nav2_controller', executable='controller_server',
            name='controller_server', output='screen',
            parameters=common_parameters,
            remappings=tf_remappings + [('cmd_vel', 'cmd_vel_nav')],
        ),
        Node(
            package='nav2_smoother', executable='smoother_server',
            name='smoother_server', output='screen',
            parameters=common_parameters, remappings=tf_remappings,
        ),
        Node(
            package='nav2_planner', executable='planner_server',
            name='planner_server', output='screen',
            parameters=common_parameters, remappings=tf_remappings,
        ),
        Node(
            package='nav2_behaviors', executable='behavior_server',
            name='behavior_server', output='screen',
            parameters=common_parameters,
            remappings=tf_remappings + [('cmd_vel', 'cmd_vel_nav')],
        ),
        Node(
            package='nav2_bt_navigator', executable='bt_navigator',
            name='bt_navigator', output='screen',
            parameters=common_parameters, remappings=tf_remappings,
        ),
        Node(
            package='nav2_waypoint_follower', executable='waypoint_follower',
            name='waypoint_follower', output='screen',
            parameters=common_parameters, remappings=tf_remappings,
        ),
        Node(
            package='nav2_velocity_smoother', executable='velocity_smoother',
            name='velocity_smoother', output='screen',
            parameters=common_parameters,
            remappings=tf_remappings + [
                ('cmd_vel', 'cmd_vel_nav'),
                ('cmd_vel_smoothed', final_cmd_vel_topic),
            ],
        ),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_navigation', output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'node_names': lifecycle_nodes,
            }],
        ),
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=str(package_share / 'config' / 'nav2_pinky_base.yaml'),
        ),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'final_cmd_vel_topic', default_value='cmd_vel',
            description='Velocity smoother output; use cmd_vel_nav_smoothed '
                        'when the vision correction layer is enabled',
        ),
        DeclareLaunchArgument(
            'autostart', default_value='false',
            description='Keep false until TF/topics/command ownership pass preflight',
        ),
        *nodes,
    ])
