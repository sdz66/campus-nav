from setuptools import find_packages, setup

package_name = 'campus_map_tools'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            # ② 锚点采集：RViz 点选 + RTK 快照 → (map_xy, wgs84) 锚点对
            'rtk_anchor_snapshot = campus_map_tools.rtk_anchor_snapshot:main',
            # ③ 对齐：Helmert 最小二乘 + 残差报告 → 写回 map.json
            'helmert_align = campus_map_tools.helmert_align:main',
            # ⑤ 出图：点云 → 栅格投影 → 人工修图辅助
            'grid_postprocess = campus_map_tools.grid_postprocess:main',
        ],
    },
)
