# vehicle · 车端域（ROS 2 Jazzy colcon 工作空间）

实现依据与权威架构：[docs/vehicle-architecture.md](../docs/vehicle-architecture.md)

```bash
cd vehicle && colcon build --symlink-install && source install/setup.bash
```

七个包：campus_msgs / campus_coord★ / campus_map_tools★ / campus_localization★ / campus_planning★ / campus_bringup / campus_gz_sim（★ 自研）。
