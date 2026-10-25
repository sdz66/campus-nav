# 中间件详细设计

> 上游：[architecture.md](architecture.md)（总体架构与量级目标）。本文是每个中间件的**选型参数、容量规划与关键配置**，落地前不再改动结构，只允许在压测后调参。

---

## 1. 接入层：长连接网关

### 1.1 选型与容量

| 项 | 设计 | 依据 |
| --- | --- | --- |
| 实现 | 自研 Netty 网关（首选）/ EMQX 企业集群（备选，快速验证期） | Netty 单实例 10 万连接（epoll + 直接内存调优），32 实例 → 320 万上限 |
| 协议 | MQTT 3.1.1 over TLS 1.3，载荷 protobuf | 位姿帧 < 100 B；弱网重连成本低 |
| 鉴权 | 连接时一次校验（设备证书 + 短期 token，token 24h 轮换） | 避免每条消息鉴权；吊销走 Redis 黑名单广播 |
| 限流 | Sentinel 接入限流：单设备 20 msg/s 硬顶 + 全局配额 | 超限丢弃并计数，不做队列堆积 |
| 会话 | 网关无业务状态；连接路由 `conn:{vin} → gateway_id` 写 Redis | 任意网关可服务任意终端，重启不丢会话语义 |

### 1.2 上下行处理

```
上行：MQTT 帧解析 → token 校验（本地缓存）→ 限流 → protobuf 解码校验
      → 异步批量写 Kafka（linger 10ms / batch 64KB / lz4）
下行：订阅 RocketMQ command（按 unit 消费）→ 查 conn 路由 → 推终端
      → 终端 ACK → 回执写 Redis（seq 水位）→ 调度引擎消费回执
```

### 1.3 上报频率自适应（车端 SDK 侧配合）

```
基础 1 Hz；速度 > 1 m/s 或进入围栏区 → 5 Hz；遥控/建图态 → 10 Hz；
Kafka 背压（网关发送队列水位）→ 全网降频广播
```

---

## 2. 消息层

### 2.1 Kafka（数据流）

| Topic | 分区 | 副本 | 保留 | 生产者 | 消费者 |
| --- | --- | --- | --- | --- | --- |
| `pose.raw.v1` | 256 | 3 | 7 天 | 网关 | Flink pose-clean |
| `pose.clean.v1` | 64 | 3 | 3 天 | Flink | 通知服务、审计 |
| `alert.v1` | 32 | 3 | 30 天 | Flink | 通知服务 |

**分区决策（ADR-001）**：`分区 = hash(vin) % 256`。50 万 msg/s ÷ 256 ≈ 2000 msg/s/分区，远低于单分区数万 msg/s 的上限——**分区数是消费并行度的天花板，不是吞吐瓶颈**；扩容只需加 Flink 并行度。单车内天然有序（定位正确性底线），车际完全并行。

**生产者配置**：`acks=all` + `enable.idempotence=true`；linger 10ms + batch 64KB + lz4（时延与吞吐平衡点，压测校准）。

**消费语义**：Flink checkpoint 对齐 Kafka offset，**端到端 exactly-once**（对 pose.clean.v1 事务写）；对 Redis/TDengine 用幂等写（upsert / 按主键覆盖）实现有效一次。

### 2.2 RocketMQ（指令流）

| 项 | 设计 |
| --- | --- |
| Topic | `TP_COMMAND.v1`（普通+事务）、`TP_COMMAND_TRACE.v1`（回执） |
| 事务消息 | 调度引擎本地事务（任务落库）+ half 消息 → 本地事务执行 → commit/rollback，**消除"落库成功投递失败"的双写不一致** |
| 定时消息 | RocketMQ 5.x 任意秒级定时：派发租约 30s = 发送时指定 30s 后投递到超时检查队列，**替代数据库轮询扫描** |
| 顺序 | 指令按 vin 分区队列（MessageQueueSelector），与上行对称 |
| 重试 | 消费失败重试 16 次退避 → 死信队列 → 人工处理台 |

---

## 3. 流计算层：Flink 作业组

| 作业 | 拓扑 | 状态与语义 | 容量规划 |
| --- | --- | --- | --- |
| `pose-clean` | Kafka(pose.raw) → keyBy(vin) → 校验/跳变剔除/降采样 → 分流 sink | keyBy 状态 = 单车滑动窗口（TTL 5 min）；checkpoint 30s，exactly-once | 50 万 msg/s ≈ 24 slots 起步（每 slot ~2 万 msg/s），HPA 按 Kafka lag |
| `fence-arbiter` | Kafka(pose.clean) + 围栏规则 broadcast 流 → keyBy(vin) → 多边形预过滤（GeoHash 网格索引）→ CEP 五态状态机 | broadcast state（规则热更新：Nacos → Kafka compacted topic）；RocksDB 增量 checkpoint | 状态 = 活跃终端数 × 状态字段，10 万终端 < 1 GB RocksDB |
| `anomaly-detect` | Kafka(pose.clean) → 轨迹漂移/静止/离线检出 → alert.v1 | 简单聚合，低优先级 | 可与 fence-arbiter 合槽 |

**围栏判定两级索引**：GeoHash 网格（精度 5，≈ 5km×5km）粗筛 → 多边形精确判定（射线法），单条 < 1 ms。

---

## 4. 存储层

### 4.1 Redis Cluster（实时状态）

| Key 模式 | 类型 | TTL | 用途 |
| --- | --- | --- | --- |
| `pose:{city}:{vin}` | Hash（lng/lat/heading/speed/state/map_version/ts） | 60 s | 实时位姿（唯一真相） |
| `geo:{city}` | ZSET（GEO） | 永久（成员随上下线增删） | 就近查询 `GEOSEARCH BYRADIUS`，P99 < 20 ms |
| `lease:{vin}:{task_id}` | String | 30 s | 派发租约 |
| `seq:{vin}` | String（INCR） | 永久 | 指令单调序号 |
| `conn:{vin}` | String | 心跳续期 | 网关连接路由 |

集群规划：**按城市分槽**（hash tag `{city}`），三主三从起步；10 万终端实时态 ≈ 10 GB 以内，单集群足够，城市数增长时按单元加集群。**Redis 是实时态唯一真相，丢数据可接受（60s 内被新上报覆盖），因此不追求持久化强度**（AOF everysec）。

### 4.2 时序库：TDengine（位姿轨迹）

| 项 | 设计 |
| --- | --- |
| 超级表 | `pose(ts, lng, lat, alt, heading, speed, state, map_version)`，TAG = `(vin, city, org_id)`，子表按 vin 自动建 |
| 写入 | Flink JDBC 批写（500 行/批）；50 万 msg/s 需 3 副本 × 8 节点起步 |
| 保留 | `KEEP 90d`；冷数据（>90 天）归档 OSS Parquet（按 city/dt 分区），评估作业读 Parquet |
| 查询 | 单车轨迹（子表裁剪）、区域热力（聚合缓存到 Redis）、误差评估离线跑 |

### 4.3 关系库：PostgreSQL + ShardingSphere（业务数据）

| 项 | 设计 |
| --- | --- |
| 分片键 | `org_id`（租户隔离与查询模式一致：所有列表查询都带 org_id） |
| 拓扑 | 16 库 × 每库 64 表（`task_{0..1023}` 等），路由 = `hash(org_id) % 1024` |
| 表族 | tasks / vehicle_grants / route_templates / remote_sessions / notification_*（与 storm-cloud schema 对齐） |
| 全局表 | organizations / users 走全局单元（不参与分片，量小） |
| 扩容 | 成对翻倍迁移（16→32 库），双写 + 对账切换 |

### 4.4 OSS + CDN（地图与文件）

- 布局：`oss://storm-maps/{city}/{map_id}/{version}/(map.pgm|map.yaml|map.json|tiles/)`
- 分发：CDN 边缘节点 + 签名 URL（15 min）；车端**增量同步**按文件哈希清单 diff，只拉差异分片
- 生命周期：版本发布后不可变；废弃版本 30 天转低频存储

---

## 5. 单元化与多活

| 项 | 设计 |
| --- | --- |
| 单元定义 | unit = city_code；设备激活时绑定 city → 写入全局路由表 |
| 单元内容 | 接入网关 / Kafka / Flink / Redis / TDengine / 域服务 **全闭环** |
| 全局单元 | 组织 / 账户 / 地图元数据（量小、强一致）；业务单元只读缓存 + 订阅变更 |
| 流量路由 | 接入按设备绑定 city 进对应单元；API 网关按 `X-City` 头路由 |
| 多活 | 同城双机房（单元主备）+ 异地灾备；单元切换 = 路由表改绑 + Kafka 消费组迁移，演练季度化 |
| 数据同步 | 全局单元 → 业务单元：DTS/CDC 订阅（最终一致，秒级） |

---

## 6. 可观测与治理

| 层 | 内容 |
| --- | --- |
| 指标 | Prometheus：分段 P99（§时延预算五段）、Kafka lag（HPA 触发源）、Redis 命中、Flink checkpoint 时长、连接数 |
| 链路 | OpenTelemetry：trace_id 贯穿 网关→Kafka→Flink→存储→终端 ACK；采样率头部 10% |
| 日志 | 结构化 JSON（trace_id/vin/city/unit），ELK |
| 配置 | Nacos（服务发现）+ Apollo（围栏规则/降级开关/限流阈值热推送） |
| 混沌 | 季度演练：杀网关节点、Kafka 分区迁移、Redis 主从切换、机房断网 |

---

## 7. 本地开发栈

`deploy/docker-compose.cloud.yml` 提供与生产同构的中间件（单节点模式）：kafka / rocketmq / flink / redis-cluster / tdengine / postgres / minio / nacos / prometheus。**本地跑通的数据契约与生产完全一致**，差别只在副本数与分区数。
