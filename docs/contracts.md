# 数据与接口契约

> 契约先行于代码（ADR-008）。本文是**全部跨服务契约的索引与规范**：消息 Schema、Kafka Topic、Redis Key、gRPC / REST 接口。改契约必须先改本文并评审，代码跟随。

---

## 1. 消息 Schema（protobuf）

统一编码 protobuf 3；包名 `storm.nav.v1`；字段只增不删不改号。

### 1.1 PoseReport（车端上行，核心报文）

```protobuf
syntax = "proto3";
package storm.nav.v1;

message PoseReport {
  string vin = 1;              // 终端标识
  string city = 2;             // 单元路由键
  int64  ts_ms = 3;            // 车端时钟（PTP 硬同步）
  double lng = 4;              // WGS84（车端出边界前已是 WGS84）
  double lat = 5;
  double alt = 6;
  float  heading = 7;          // 0-360
  float  speed = 8;            // m/s
  uint32 gps_status = 9;       // RTK 状态（4 = fixed）
  uint8  loc_state = 10;       // 车端仲裁五态（枚举同 LocalizationStatus）
  string map_id = 11;
  string map_version = 12;
  float  cov_x = 13;           // 协方差对角线（x/y/yaw）
  float  cov_y = 14;
  float  cov_yaw = 15;
  uint32 seq = 16;             // 单车单调递增（乱序/重复检测）
}
```

### 1.2 Command（云端下行）

```protobuf
message Command {
  string vin = 1;
  uint64 seq = 2;              // 全局单调，终端去重依据
  int64  issue_ts_ms = 3;
  oneof payload {
    TaskDispatch task = 10;        // 任务派发（含 navigationData）
    TaskCancel cancel = 11;        // 两阶段取消
    MapSync    map_sync = 12;      // 地图版本通知（增量清单哈希）
    ControlCtl control = 13;       // pause/resume/灯/喇叭
    Frequency  freq = 14;          // 上报频率调整（背压广播）
  }
}

message CommandAck {
  string vin = 1;
  uint64 seq = 2;              // 对应 Command.seq
  bool   accepted = 3;
  int64  ack_ts_ms = 4;
}
```

### 1.3 LocalizationStatus（车端内部 + 上行状态）

与 `vehicle/src/campus_msgs/msg/LocalizationStatus.msg` 字段一一对应：`state ∈ {0 NOMINAL, 1 GNSS_DEGRADED, 2 SCAN_LOST, 3 DEAD_RECKONING, 4 LOST}`。

---

## 2. Kafka Topic 契约

| Topic | Key | 载荷 | 分区/副本 | 保留 | 生产者 → 消费者 |
| --- | --- | --- | --- | --- | --- |
| `pose.raw.v1` | vin | PoseReport | 256 / 3 | 7d | 网关 → Flink pose-clean |
| `pose.clean.v1` | vin | PoseReport（清洗后） | 64 / 3 | 3d | Flink → 通知/审计 |
| `alert.v1` | vin | Alert | 32 / 3 | 30d | Flink → 通知服务 |
| `fence.rules.v1` | scene_id | FenceRule（compacted） | 8 / 3 | compacted | 规则发布 → Flink broadcast |
| `map.meta.v1` | map_id | MapMetaEvent（compacted） | 8 / 3 | compacted | 地图服务 → 各订阅方 |

**演进规则**：只允许新增 `*.v2` 并行双写，消费方切换后下线 v1；禁止原地改字段语义。

---

## 3. RocketMQ 契约

| Topic | 类型 | 载荷 | 说明 |
| --- | --- | --- | --- |
| `TP_COMMAND.v1` | 事务消息 | Command | 调度引擎 half 消息 → 本地事务 → commit；按 vin 选择队列 |
| `TP_COMMAND_TIMEOUT.v1` | 定时消息 | LeaseTimeout | 发送时指定 30s 后投递 = 租约到期检查（RocketMQ 5 定时精度 1s） |
| `TP_COMMAND_TRACE.v1` | 普通 | CommandAck | 终端 ACK 回执，调度引擎消费推进状态机 |

---

## 4. Redis Key 规范

| Key 模式 | 类型 | TTL | 写方 → 读方 | 说明 |
| --- | --- | --- | --- | --- |
| `pose:{city}:{vin}` | Hash | 60s | Flink → 查询服务 | 实时位姿唯一真相 |
| `geo:{city}` | ZSET(GEO) | — | Flink → 查询服务/调度 | 成员 vin，GEOSEARCH 就近 |
| `lease:{vin}:{task_id}` | String | 30s | 调度 → 调度 | 派发租约 |
| `seq:{vin}` | String | — | 网关 → 网关 | 下行指令单调序号 |
| `conn:{vin}` | String | 心跳续期 | 网关 → 网关 | 连接路由（gateway_id） |
| `cmd_watermark:{vin}` | String | — | 终端 ACK → 调度 | 已确认 seq 水位 |
| `ratelimit:{vin}` | String | 1s 窗口 | 网关 | 令牌桶计数 |

命名纪律：一律小写、`:` 分层、首段为数据域；禁止在业务代码里拼私有 key（统一走各服务的 Repository 层）。

---

## 5. gRPC 接口（云端内部）

| 服务 | 方法 | 请求 → 响应 | 说明 |
| --- | --- | --- | --- |
| LocationQuery | `GetPose(vin)` | → PoseSnapshot | 实时位姿（Redis 路径，P99 < 20 ms） |
| LocationQuery | `GetTrack(vin, from, to)` | → stream PoseReport | 轨迹（TDengine，异步流式） |
| LocationQuery | `SearchNearby(city, lng, lat, radius, filter)` | → stream PoseSnapshot | GEO 就近（调度引擎高频调用） |
| CoordinateService | `ToMap(city, map_id, wgs84)` / `ToWgs84(...)` | 纯转换 | 无状态水平扩（ADR-007） |
| PlanningService | `PlanRoute(map_id, start, targets, policy)` | → NavigationData | 高德 60s 超时同款语义 |
| MapSync | `DiffCheck(map_id, version, hashes)` | → Delta | 车端增量同步清单 |

---

## 6. REST 接口（对外，复用 storm-cloud 契约）

对外 REST 沿用 storm-cloud 已冻结的契约（全 POST + `{code,msg,data}` 信封 + 339 错误码 + 游标分页，见 `starj-console-api-docs/`）。本平台新增/演进的部分：

| 路径 | 演进 | 说明 |
| --- | --- | --- |
| `/storm/v3/nodes/location` | → C4 定位查询 | 契约不变，实现从单库查询换 Redis 路径 |
| `/storm/v3/maps/*`（19 条） | → C3 地图服务 | 契约不变，fileKey 换 OSS+CDN 签名 URL |
| `/storm/v3/tasks/queue/dispatch/*` | → C6 调度引擎 | 契约不变，租约扫描换定时消息 |
| `/storm/v3/data/taskList` | → C4 | 快照分页语义保持 |

---

## 7. 车端话题契约（ROS 2，车端域内部）

车端话题表与消息定义见 [vehicle-architecture.md](vehicle-architecture.md) §3。车云边界只有两条：**上行 PoseReport（MQTT）**、**下行 Command（MQTT）**——ROS 话题不跨出车端。

---

## 8. 兼容性纪律

1. 契约变更流程：改本文 → 评审 → 生成代码（buf/protoc）→ 双写灰度
2. protobuf 字段：只增不改号不删；废弃字段标 `deprecated` 保留两个版本周期
3. 枚举：只增不改值；未知值消费方必须落入兜底分支（与前端处理未知错误码同款纪律）
4. 所有生产者必须带 `schema 版本头`（消息 envelope：`schema_version` 字段，首个字段）
