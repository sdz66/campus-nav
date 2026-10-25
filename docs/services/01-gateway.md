# C1 接入网关（gateway）

> 设计文档；代码目录 [cloud/gateway/](../../cloud/gateway/)（A2 阶段开工，本页为唯一实现依据）。

## 职责边界

**做**：百万级 MQTT 长连接的接入、鉴权、限流、上下行编解码、连接路由。
**不做**：业务逻辑（位姿处理归 C2、指令生成归 C6）——网关是纯数据搬运层。

## 接口

| 方向 | 协议 | 契约 |
| --- | --- | --- |
| 上行 | MQTT `up/pose/{vin}` | PoseReport（contracts.md §1.1）→ Kafka `pose.raw.v1` |
| 下行 | MQTT `down/cmd/{vin}` | Command ← RocketMQ `TP_COMMAND.v1` |
| ACK | MQTT `up/ack/{vin}` | CommandAck → Redis 水位 + `TP_COMMAND_TRACE.v1` |
| 内部 | gRPC `GatewayAdmin` | 踢下线、广播降频、连接数查询 |

## 数据模型

- 连接表：`conn:{vin} → gateway_id`（Redis，心跳续期 30s）
- 会话态：本地内存（订阅关系、in-flight 窗口），进程重启即重建
- 不持久化任何业务数据

## 关键设计

1. **单实例 10 万连接**：Netty epoll + 直接内存池 + 写合并（同 vin 高频帧聚合 flush）
2. **背压传导**：本地发送队列水位 > 70% → 上报 Kafka 网关健康流 → 全网降频广播（Command.freq）
3. **优雅发布**：连接路由在 Redis，滚动重启先摘流量排空连接（drain 5min）
4. **鉴权**：连接时 mTLS + token 双因子；吊销走 Redis 黑名单 + 广播失效

## 部署

无状态（除本地会话），K8s Deployment 32 副本起步，HPA 按连接数 + 发送队列水位；独立于业务服务的发布节奏（遥控链路不能因业务发布重启）。

## 降级

Sentinel 全局限流；Kafka 不可用时本地环形缓冲（100k 帧）+ 延迟重试；Redis 不可用时拒绝新连接、保存量连接（降级为单网关直连语义）。

## 验收

- 100 万模拟终端连接（32 实例），CPU < 60%
- 上行 50 万 msg/s 持续 30 min，Kafka lag 无累积
- 单实例 kill，终端 5s 内重连到其他实例，无消息丢失（seq 连续）
