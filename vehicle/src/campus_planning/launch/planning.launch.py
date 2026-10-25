#!/usr/bin/env python3
"""规划栈：Nav2 全家桶（planner/controller/bt_navigator/costmaps）+ 高德链路节点。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

from ament_index_python.packages import get_package_share_directory

PKG = 'campus_planning'
NAV2 = 'nav2_bringup'


def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim_time')
    pkg_share = get_package_share_directory(PKG)
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory(NAV2), 'launch', 'navigation_launch.py')),
            launch_arguments={
                'use_sim_time': use_sim,
                'params_file': os.path.join(pkg_share, 'config', 'nav2_params.yaml'),
            }.items(),
        ),
        # amap_client / route_converter / goal_server 按需启动（N4 交付后接入）
    ])
