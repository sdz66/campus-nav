# C6 调度引擎（dispatch）

> 设计文档；代码目录 [cloud/dispatch/](../../cloud/dispatch/)。上游契约：storm-cloud `tasks/*`、`tasks/queue/*`（11 条，契约不变）。这是 storm-cloud 派发逻辑的规模化演进：DB 轮询扫描 → RocketMQ 定时消息。

## 职责边界

**做**：任务-车辆匹配（就近指派）、派发租约、重试与人工兜底、队列管理事件化。
**不做**：任务 CRUD（storm-cloud 契约层已有）、路径规划（C5）、终端连接（C1）。

## 接口

| 层 | 接口 | 语义 |
| --- | --- | --- |
| 事件消费 | `pose.clean.v1`（车辆状态变化）、`TP_COMMAND_TRACE.v1`（ACK 回执） | 状态机推进的事件源 |
| 事件生产 | `TP_COMMAND.v1`（事务消息）、`TP_COMMAND_TIMEOUT.v1`（定时消息） | 指令下发与租约超时 |
| REST 对外 | `tasks/create` / `cancel` / `queue/*`（11 条） | storm-cloud 契约原样，信封/错误码/幂等语义不变 |
| gRPC 内部 | `SearchNearby`（C4） | 就近指派的候选检索 |

## 状态机（与 storm-cloud 六章对齐）

```
创建 → [策略判定] → Running(空闲直发) / Pending(入队)
Pending → 车辆空闲 → 派发（事务消息：任务落库+投递原子）→ 租约 30s（定时消息）
  ├─ ACK（TP_COMMAND_TRACE）→ Accepted → Running
  ├─ 租约超时（定时消息触发）→ attempt+1 重试（1s/3s/9s 退避）
  └─ attempt ≥ 3 → needs_resolution → 人工兜底队列（契约 queue/dispatch/resolve）
取消 → 两阶段：Canceling + cancel_pending → ACK → Canceled
```

## 关键设计

1. **事务消息**：任务状态落库与指令投递原子（half → local tx → commit），消除双写不一致
2. **租约 = 定时消息**：RocketMQ 5 秒级定时，无扫描；租约检查无状态可水平扩（ADR-006）
3. **就近指派**：C4 `SearchNearby`（Redis GEO，P99 < 20 ms）取候选 → 本地过滤（空闲/电量/地图版本/任务占用）→ 距离排序 → 事务落库
4. **队列事件化**：队列重排仍走契约的乐观锁 version（REST 同步语义），内部变更以事件广播到 Flink/通知
5. **幂等**：指令 seq 单调（Redis INCR）；`idempotency_key` 唯一约束防重复创建（契约已有）

## 数据模型

分库分表（org_id 路由）：tasks / vehicle_queues；Redis：lease / seq / cmd_watermark。**调度过程状态全部在 Redis + RocketMQ，DB 只存事实**（任务与队列的最终状态）。

## 部署

无状态消费者组，16 副本起步（RocketMQ 消费并行度按队列数）；与 Redis/RocketMQ 同单元。

## 降级

RocketMQ 不可用 → 拒绝新派发（存量任务车端自治完成当前任务）；Redis 不可用 → 暂停派发（租约无法续期，宁可不动不可乱动）；C4 不可用 → 指派降级为队列顺序派发。

## 验收

- 5 万 TPS 指令下发稳定；事务消息无双写不一致（对账任务 0 差异）
- 租约超时触发误差 < 2 s（30s 租约）
- 1000 任务/100 车压测：零重复派发（seq 对账）、零丢失（终态对账）
