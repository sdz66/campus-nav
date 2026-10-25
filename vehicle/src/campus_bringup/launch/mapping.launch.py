#!/usr/bin/env python3
"""建图：SLAM Toolbox 在线建图 + RTK 全程记录（W2 建图 SOP ①）。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    map_name = LaunchConfiguration('map_name')
    slam = Node(
        package='slam_toolbox', executable='async_slam_toolbox_node',
        name='slam_toolbox', output='screen',
        parameters=[{'use_sim_time': False, 'mode': 'mapping'}],
    )
    rtk_log = Node(
        package='campus_map_tools', executable='rtk_anchor_snapshot.py',
        name='rtk_logger', output='screen',
        parameters=[{'log_alongside': True}],   # 建图全程记录 RTK 轨迹
    )
    return LaunchDescription([
        DeclareLaunchArgument('map_name', default_value='campus-draft'),
        slam,
        rtk_log,
    ])
