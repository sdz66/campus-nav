# 架构设计 · campus-nav

> **车端域详细架构**（ROS 2 Jazzy）。平台总体架构见 [architecture.md](architecture.md)，中间件见 [middleware.md](middleware.md)，云端域服务见 [services/](services/)。需求原件见 [requirements/](requirements/)。
> 版本：2026-10-25 v2（平台量级重构，车端域拆分）

---

## 1. 需求与架构映射

《导航定位模块.pdf》定义三块：

1. **全局基准（离线准备）**：激光 SLAM（稀疏点云建图）+ 多点 RTK（赋予地图全局经纬度与基准朝向）+ 校园特殊场景标定（map 可读 JSON）。目标：生成 ROS 2 二维栅格地图。
2. **坐标体系**：高德（GCJ-02）+ RTK（WGS84）+ 离线地图（局部笛卡尔）三套坐标对应关系。
3. **全局规划**：高德地图 → 坐标转换至离线地图 → 输出全局参考路径。
4. **行驶定位**：基准地图 + 激光点云匹配 + IMU + 轮速计（三者递推输出局部位姿）+ RTK 经纬度校正 → 输出实时位姿。

架构结论：**采用三源融合定位架构**——激光点云匹配（短时修正）+ 轮速/IMU 航位推算（连续递推）+ RTK 经纬度校正（全局无漂移），全部用成熟开源包组合，自研仅四个薄胶水层。

---

## 2. 坐标体系（最先做，全系统的地基）

### 2.1 四层坐标系

| 层 | 定义 | 载体 |
| --- | --- | --- |
| `gcj02` | 高德加密经纬度 | 仅出现在高德 API 边界 |
| `wgs84` | RTK 原始经纬度 | `navsat_transform` 输入 |
| `enu` | 以 datum 为原点的局部笛卡尔（米） | GeographicLib LocalCartesian |
| `map` | 栅格地图像素系（原点平移 + 基准朝向旋转） | 所有算法唯一工作系 |

### 2.2 map.json（自研，唯一自定义格式）

```json
{
  "map_id": "hohai-campus-v1",
  "version": "2026.11.30-rc1",
  "datum": {
    "wgs84": { "lat": 31.8639, "lon": 118.6080, "alt": 12.4 },
    "heading_deg": 87.3,
    "enu_frame": "campus_enu"
  },
  "anchors": [
    { "id": "gcp-01", "type": "rtk_anchor",
      "wgs84": { "lat": 31.8641, "lon": 118.6083, "alt": 12.5 },
      "map_xy": [23.45, -8.12],
      "residual_m": 0.04,
      "collected_at": "2026-11-20T09:30:00+08:00" }
  ],
  "grid": { "pgm": "map.pgm", "yaml": "map.yaml", "resolution_m": 0.05 },
  "problem_scenes": [
    { "id": "scene-wutong", "type": "gnss_denied",
      "polygon_map_xy": [[0,0]], "note": "梧桐路树荫带，RTK 退化区" }
  ],
  "accuracy": { "anchor_rmse_m": 0.06, "method": "helmert_similarity" }
}
```

**一个 JSON 服务四方**：`navsat_transform` 的 datum、建图对齐锚点、云端 `maps/*` 元数据上传、定位降级的退化区 polygon。

### 2.3 转换实现

| 转换 | 实现 | 说明 |
| --- | --- | --- |
| GCJ-02 → WGS84 | 高德官方转换 API（主）+ 公开算法（兜底/交叉校验） | 合规优先；差异报告进 CI |
| WGS84 → ENU | GeographicLib `LocalCartesian`（C++）/ pyproj（离线工具） | datum = map.json.datum |
| ENU → map | map.json 的原点平移 + heading 旋转 | 建图期 Helmert 相似变换解算 |

**红线**：坐标链闭合误差 < 0.1 m（已知控制点全链路往返），W2 验证，不过不放行后续模块。

---

## 3. 节点图与话题

### 3.1 车端运行时节点

```
传感器驱动
  ├── lidar_driver ──/scan (2D) 或 /points (3D)
  ├── imu_driver   ──/imu/data
  ├── chassis      ──/wheel_odom  (轮速计)
  └── rtk_driver   ──/gps/fix (NTRIP 差分)

定位栈
  ├── campus_localization/ekf_local   (robot_localization ekf_node, 轮速+IMU → odom→base_link)
  ├── nav2_amcl                       (基准地图点云匹配 → map→odom 修正)
  ├── campus_localization/navsat      (robot_localization navsat_transform_node, RTK → ENU)
  ├── campus_localization/ekf_global  (双 EKF 全局链 → map→odom)
  └── campus_localization/pose_arbiter ★ (仲裁 → /localization/pose + /localization/status)

规划栈
  ├── campus_planning/amap_client ★     (高德 REST，mock 模式供 CI)
  ├── campus_planning/route_converter ★ (GCJ-02 → map 系参考路径)
  ├── campus_planning/goal_server ★     (任务系统/APP 选点 → Nav2 goal)
  └── nav2 (planner Smac Hybrid-A* / controller RPP|DWB / bt_navigator / behavior)
```

### 3.2 核心话题表

| 话题 | 类型 | 频率 | 生产者 → 消费者 |
| --- | --- | --- | --- |
| `/scan` | `sensor_msgs/LaserScan` | 10 Hz | 雷达 → AMCL/SLAM |
| `/imu/data` | `sensor_msgs/Imu` | 100 Hz | IMU → 双 EKF |
| `/wheel_odom` | `nav_msgs/Odometry` | 50 Hz | 底盘 → ekf_local |
| `/gps/fix` | `sensor_msgs/NavSatFix` | 1 Hz | RTK → navsat_transform |
| `/odom` | `nav_msgs/Odometry` | 50 Hz | ekf_local → 控制器 |
| `/localization/pose` | `geometry_msgs/PoseWithCovarianceStamped` | 50 Hz | ekf_global → Nav2/云端上报 |
| `/localization/status` | `campus_msgs/LocalizationStatus` | 1 Hz | pose_arbiter → 安全逻辑/云端 |
| `/global_reference_path` | `nav_msgs/Path` | 按需 | route_converter → Nav2 代价先验 |
| `/cmd_vel` | `geometry_msgs/Twist` | 20 Hz | controller → 底盘 |

### 3.3 自定义消息

```
# campus_msgs/LocalizationStatus.msg
std_msgs/Header header
uint8 state          # NOMINAL/GNSS_DEGRADED/SCAN_LOST/DEAD_RECKONING/LOST
float32[3] covariance_diag   # 定位协方差对角线（x,y,yaw）
float32 rtk_hdop
string map_id
string map_version
---
# 状态枚举常量
uint8 NOMINAL=0
uint8 GNSS_DEGRADED=1
uint8 SCAN_LOST=2
uint8 DEAD_RECKONING=3
uint8 LOST=4
```

```
# campus_msgs/MapMeta.msg（map.json 的运行时投影）
string map_id
string version
float64[3] datum_wgs84      # lat, lon, alt
float64 heading_deg
string venue_file_path
string[] problem_scene_ids
```

---

## 4. 建图工具链 SOP（campus_map_tools）

```
① 采集    推车/低速车绕场 2~3 圈（正反双向），SLAM Toolbox 在线建图，
          RTK 全程记录；重点区域（岔路/广场/树荫带）减速多走几遍
② 锚点    停在预设控制点（≥6 个，四角+中心），每点静态采集 RTK 30s 取均值，
          同时记录当时 SLAM 位姿 → 得到 (map_xy, wgs84) 锚点对
③ 对齐    Helmert 相似变换（平移+旋转+缩放）最小二乘解算 map→ENU，
          残差 RMSE 写入 map.json（验收 < 0.15 m）
④ 定朝向  两个相距最远的锚点连线确定基准朝向 heading_deg
⑤ 出图    点云→栅格投影→人工修图（去飞点/补墙）→ map.pgm + yaml + json
⑥ 场景    GNSS 退化区 polygon、特殊场景写入 problem_scenes
```

**第 0 步**：底盘标定（轮距/脉冲当量）——轮速计未标定会污染 EKF（风险 M5）。

## 5. 定位栈详细设计

### 5.1 双 EKF

| 链 | 输入 | 输出 | 特性 |
| --- | --- | --- | --- |
| 局部链 `ekf_local` | 轮速 + IMU | `odom→base_link`（/odom） | 连续高频，短时可信，与 map 无关 |
| 全局链 `ekf_global` | AMCL 位姿 + RTK（经 navsat） | `map→odom` 修正 | 无长期漂移，低频修正 |

### 5.2 仲裁状态机（pose_arbiter）

```
                    ┌──────────────────────────────┐
                    │        NOMINAL               │
                    │ AMCL 得分正常 + RTK fixed     │
                    └──┬──────────────┬────────────┘
         进入退化 polygon│              │ AMCL 得分 < 阈值 N 帧
                       ▼              ▼
        ┌──────────────────┐      ┌──────────────┐
        │ GNSS_DEGRADED    │      │ SCAN_LOST    │
        │ RTK 权重→0       │─────▶│ 仅航位推算    │
        │ 仅 AMCL          │ 恢复 │ 告警          │
        └──────────────────┘      └──────┬───────┘
                                          │ 超时
                                          ▼
                                   ┌──────────────┐
                                   │DEAD_RECKONING│──超时──▶ LOST（安全停车+云端告警）
                                   └──────────────┘
```

**实现要点**：
- RTK 质量门控：`gpsStatus`（4 = RTK fixed）+ hdop 双条件
- AMCL 得分滑动窗口均值，避免单帧抖动
- 状态迁移写日志（含触发原因），供 PlotJuggler 误差归因

### 5.3 调参顺序（M3）

仿真先粗调（Gazebo 注入 GNSS 噪声模拟树荫 multipath）→ 实车精调；PlotJuggler 四联图（定位误差 / AMCL 得分 / RTK 状态 / EKF 协方差）为标准工具。

## 6. 规划栈详细设计

### 6.1 分层规划

```
路网级   高德路径 API（校门→楼栋的外部路段，GCJ-02 折线）
   ↓ route_converter：GCJ-02 → WGS84 → ENU → map 系
校内级   自建车道图（map.json internal_routes；校园内部道路高德没有！）
栅格级   Nav2 Smac Hybrid-A*（参考路径作为代价先验）
执行级   Nav2 controller（RPP/DWB）+ bt_navigator 行为树
```

### 6.2 最高优先级风险

**高德路网不含校园内部道路**（M1）。W3 前必须完成校内车道图方案：从建图成果半自动提取道路中心线，存入 map.json 的 `internal_routes` 扩展段，作为栅格级规划的先验。

## 7. 仿真与测试

| 层 | 工具 | 内容 |
| --- | --- | --- |
| 传感器仿真 | Gazebo Harmonic + ros_gz | GNSS 区域噪声模型（树荫 multipath）、激光/IMU/轮速 |
| 回放回归 | rosbag2 | 实车录制 → 离线重放定位栈（改参数不上车） |
| 指标看板 | PlotJuggler | 四联图模板（tools/plotjuggler/） |
| CI 门禁 | GitHub Actions | ros:jazzy 容器 colcon build+test；仿真冒烟 5 路线+3 退化场景 |

## 8. 验收指标

| 指标 | 目标 | 测法 |
| --- | --- | --- |
| 锚点对齐 RMSE | < 0.15 m | map.json 的 Helmert 残差 |
| 定位横向误差（RTK fixed） | RMSE < 0.3 m | RTK 真值 vs 输出位姿（离线评估） |
| 定位横向误差（GNSS 退化区） | RMSE < 0.5 m | 按 polygon 切片统计 |
| 位姿连续性 | 单帧跳变 < 0.2 m | 全程 max-jump 统计 |
| 定位可用率 | > 99%（非 LOST） | 状态占比 |
| 高德链路时延 | P95 < 2 s | API 计时 |
| 仿真回归 | 100% 通过 | CI 门禁 |

## 9. 风险登记册

| # | 风险 | 概率 | 影响 | 缓解 |
| --- | --- | --- | --- | --- |
| M1 | 高德无校内路网 | 高 | 高 | W3 前定校内车道图方案 |
| M2 | 树荫 multipath 致 RTK 跳变 | 高 | 高 | 退化 polygon + 仲裁降级 + NTRIP 质量监控 |
| M3 | GCJ-02 转换误差 | 中 | 中 | 官方 API 为主 + 交叉校验报告 |
| M4 | AMCL 大面积相似场景失配 | 中 | 高 | 退化区参考线；必要时上 NDT/small_gicp |
| M5 | 轮速计未标定污染 EKF | 中 | 中 | 建图 SOP 第 0 步：底盘标定 |
| M6 | 地图过期（校园施工） | 中 | 中 | map.json 版本化 + 云端下发 |
| M7 | 2D/3D 激光选型未定 | 中 | 高 | W1 确认硬件；3D 走 LIO-SAM+NDT 路线 |

## 10. 与 storm-cloud 的对接（节选）

| 模块产物 | 云端接口 | 说明 |
| --- | --- | --- |
| map.pgm/yaml/json | `maps/upload`、`maps/publish` | map.json 随包上传 |
| `/localization/pose` | `nodes/location` 上报 | 含协方差与状态 |
| `LOST` 持续 | 云端告警 + 遥控接管 | 对接遥控链路 |
| 高德参考路径 | 任务 `navigationData.route` | 透传 |
| 地图版本 | OTA 分片通道 | 版本化下发 |
