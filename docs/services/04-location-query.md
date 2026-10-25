# C4 定位查询服务（location-query）

> 设计文档；代码目录 [cloud/location-query/](../../cloud/location-query/)。上游契约：storm-cloud `nodes/location`、`nodes/positioning-status/batch`（契约不变）。

## 职责边界

**做**：实时位置查询、轨迹查询、就近检索、批量定位状态。
**不做**：位姿写入（C2）、调度决策（C6）。

## 接口

| 层 | 接口 | 语义 |
| --- | --- | --- |
| gRPC 内部 | `GetPose(vin)` | 实时位姿，Redis 路径，P99 < 20 ms |
| gRPC 内部 | `SearchNearby(city, lng, lat, radius, filter)` | GEOSEARCH 就近，调度引擎高频调用 |
| gRPC 内部 | `GetTrack(vin, from, to)` | 轨迹流式返回（TDengine） |
| REST 对外 | `nodes/location`、`positioning-status/batch` | storm-cloud 契约原样 |

## 读路径

```
GetPose:  Redis pose:{city}:{vin}            （热路径，命中 > 99.9%，60s TTL）
  miss → TDengine 最近一条（冷路径，P99 放宽 200ms + 告警）
GetTrack: TDengine 子表裁剪（vin 索引）→ 流式返回
SearchNearby: GEOSEARCH geo:{city} → 批量 GetPose 补全 → 过滤
```

## 关键设计

1. **读放大治理**：SearchNearby 先 GEO 半径筛（内存）再批量 MGET 位姿，两跳都在 Redis
2. **城市路由**：请求带 city（或由 vin 查全局路由表），跨城市查询走全局单元代理
3. **一致性语义**：实时位姿是"最后写入胜出"（Flink 单写者），无并发冲突；`ts_ms` 随响应返回供调用方判断新鲜度
4. **批量接口**：`positioning-status/batch` 上限 200（契约），内部 pipeline 批量取

## 部署

无状态 gRPC 服务，12 副本起步（HPA 按 QPS）；与 Redis/TDengine 同单元部署。

## 降级

Redis 不可用 → TDengine 最近值路径（性能降级，功能不降级）；TDengine 不可用 → 仅实时态可用，轨迹接口返回明确错误码。

## 验收

- GetPose P99 < 20 ms（10 万 QPS）
- SearchNearby P99 < 20 ms（1 万 QPS，半径 5km 命中 1000 成员）
- 轨迹查询 90 天范围单车 < 500 ms
