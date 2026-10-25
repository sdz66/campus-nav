#!/usr/bin/env python3
"""仿真冒烟：Gazebo Harmonic + Nav2 全家桶（CI 门禁载体）。

用法: ros2 launch campus_bringup simulation.launch.py
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    gz_world = LaunchConfiguration('world')
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='campus'),

        # Gazebo Harmonic 世界 + 校园机器人
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('campus_gz_sim'), 'launch', 'gz_sim.launch.py')),
            launch_arguments={'world': gz_world}.items(),
        ),

        # 定位栈（仿真噪声版参数）
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('campus_localization'), 'launch', 'localization.launch.py')),
            launch_arguments={'use_sim_time': 'true'}.items(),
        ),

        # 规划栈（Nav2）
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('campus_planning'), 'launch', 'planning.launch.py')),
            launch_arguments={'use_sim_time': 'true'}.items(),
        ),
    ])
