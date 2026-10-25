# C2 位姿管道（pipeline）

> 设计文档；代码目录 [cloud/pipeline/](../../cloud/pipeline/)（Flink 作业组）。

## 职责边界

**做**：位姿清洗去噪、围栏判定、云端仲裁镜像、异常检测、多存储落库。
**不做**：业务查询（C4）、规则定义（规则来自地图服务 C3 的 fence.rules.v1 流）。

## 作业拓扑

| 作业 | 输入 → 输出 | 算子要点 |
| --- | --- | --- |
| `pose-clean` | `pose.raw.v1` → Redis + TDengine + `pose.clean.v1` | keyBy(vin) → 合法性校验（坐标范围/时间戳窗口）→ 跳变剔除（速度上限门控）→ 降采样（下游按需 1~5 Hz） |
| `fence-arbiter` | `pose.clean.v1` + `fence.rules.v1`(broadcast) → 状态流 + 告警 | GeoHash 粗筛 → 多边形精确判定 → CEP 五态状态机（车端仲裁的云端镜像，ADR-003） |
| `anomaly-detect` | `pose.clean.v1` → `alert.v1` | 轨迹漂移 / 长时间静止 / 离线检出 |

## 数据模型（写入面）

- Redis：`pose:{city}:{vin}` Hash（60s TTL）、`geo:{city}` GEO 成员
- TDengine：超级表 `pose` 子表按 vin，Flink JDBC 500 行/批
- Kafka：`pose.clean.v1`（事务写，exactly-once）

## 语义与一致性

- checkpoint 30s，Kafka 事务写 + Redis/TDengine 幂等 upsert = 有效一次
- 乱序处理：允许 5s 事件时间乱序（watermark），更晚数据进侧输出旁路供审计
- 车端 `seq` 重复/回退 → 丢弃 + 计数（终端时钟异常指标）

## 部署

K8s（Flink Kubernetes Operator），pose-clean 24 slots 起步，HPA 按 `pose.raw.v1` 消费 lag；RocksDB 增量 checkpoint 到 OSS。

## 降级

Flink 作业故障：Kafka 保留 7 天位姿，恢复后从 checkpoint/最早未消费位点追平；Redis 不可用 → 只写 TDengine（实时查询退化到 TSDB 最近值路径，P99 放宽到 200ms 并告警）。

## 验收

- 50 万 msg/s 稳态，checkpoint < 10s，无 backpressure
- 围栏判定单条 < 1 ms（GeoHash 预过滤命中率 > 95%）
- 混沌：kill TaskManager，恢复后无数据丢失（seq 连续性校验）
