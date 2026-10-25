#!/usr/bin/env python3
"""Gazebo Harmonic 启动：campus 世界 + 机器人 + ros_gz 桥接。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import os

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    world = LaunchConfiguration('world')
    gz_launch = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    world_file = os.path.join(get_package_share_directory('campus_gz_sim'), 'worlds', 'campus.sdf')
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='campus'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(gz_launch),
                                 launch_arguments={'gz_args': f'-r {world_file}'}.items()),
        # ros_gz_bridge：/scan /imu /gps/fix /cmd_vel（W5 交付）
    ])
