#!/usr/bin/env python3
"""实车/实图运行：定位栈 + 规划栈 + Nav2（map 参数指定版本化地图目录）。

用法: ros2 launch campus_bringup vehicle.launch.py map:=campus-v1
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    map_dir = LaunchConfiguration('map')
    return LaunchDescription([
        DeclareLaunchArgument('map', default_value='campus-v1'),

        # 地图（maps/ 目录的 pgm/yaml/json 三件套）
        Node(
            package='nav2_map_server', executable='map_server', output='screen',
            parameters=[{'yaml_filename': PathJoinSubstitution(['maps', map_dir, 'map.yaml'])}],
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                FindPackageShare('campus_localization').find('campus_localization'),
                'launch', 'localization.launch.py')),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                FindPackageShare('campus_planning').find('campus_planning'),
                'launch', 'planning.launch.py')),
        ),
    ])
