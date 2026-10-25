#!/usr/bin/env python3
"""定位栈：双 EKF + AMCL + navsat_transform + pose_arbiter（三源融合）。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

from ament_index_python.packages import get_package_share_directory

PKG = 'campus_localization'


def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim_time')
    pkg_share = get_package_share_directory(PKG)
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        Node(package='robot_localization', executable='ekf_node', name='ekf_local',
             parameters=[os.path.join(pkg_share, 'config', 'ekf_local.yaml'),
                         {'use_sim_time': use_sim}], output='screen'),
        Node(package='robot_localization', executable='ekf_node', name='ekf_global',
             parameters=[os.path.join(pkg_share, 'config', 'ekf_global.yaml'),
                         {'use_sim_time': use_sim}], output='screen'),
        Node(package='nav2_amcl', executable='amcl', name='amcl',
             parameters=[os.path.join(pkg_share, 'config', 'amcl.yaml'),
                         {'use_sim_time': use_sim}], output='screen'),
        # navsat_transform（datum 来自 map.json，W2 后注入）+ pose_arbiter（N3 交付）
        Node(package=PKG, executable='pose_arbiter', name='pose_arbiter', output='screen'),
    ])
