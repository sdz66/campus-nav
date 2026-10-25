from setuptools import find_packages, setup

package_name = 'campus_planning'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/nav2_params.yaml']),
    ],
    install_requires=['setuptools', 'requests', 'pyproj'],
    entry_points={
        'console_scripts': [
            # 高德路径 → map 系参考路径（带 mock 模式供 CI，不打真接口）
            'amap_client = campus_planning.amap_client:main',
            # GCJ-02 折线 → WGS84 → ENU → map 系 Path
            'route_converter = campus_planning.route_converter:main',
            # 任务系统/APP 选点（GCJ-02）→ Nav2 goal
            'goal_server = campus_planning.goal_server:main',
        ],
    },
)
