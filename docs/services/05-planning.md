# C5 规划服务集群（planning）

> 设计文档；代码目录 [cloud/planning/](../../cloud/planning/)。车端配套：`vehicle/src/campus_planning/`（客户端 + 车内兜底）。

## 职责边界

**做**：分层规划编排（外部高德路网 + 校内车道图 + 栅格细化）、navigationData 生成、规划缓存。
**不做**：路径执行（Nav2 在车端）、地图数据生产（C3）。

## 接口

| 层 | 接口 | 语义 |
| --- | --- | --- |
| gRPC 内部 | `PlanRoute(map_id, start, targets, policy)` | → NavigationData（契约同 storm-cloud `maps/navigation/line`） |
| gRPC 内部 | `PlanEta(route)` | → duration_s / distance_m |
| REST 对外 | `maps/navigation/line`（60s 超时） | storm-cloud 契约原样 |

## 分层规划

```
路网级   高德 API（外部路段，GCJ-02）── Sentinel 熔断 + 限流 + 双实现交叉校验
校内级   自建车道图（map.json internal_routes，从建图成果提取中心线）
栅格级   参考路径作为代价先验（实际细化由车端 Nav2 完成——云不替代车）
```

**云车分工原则**：云端产出**参考路径**（navigationData 契约原样透传给任务系统），可执行轨迹由车端 Nav2 基于本地地图细化——云端断供时车端仍可按车道图行驶。

## 关键设计

1. **规划缓存**：`(map_id, version, start_grid, targets)` 哈希 → 结果缓存 Redis TTL 10 min（同图同起终点复用）
2. **外部依赖治理**：高德 API 双实现（官方/公开算法）、Sentinel 熔断、mock 模式供 CI（契约测试不打真接口）
3. **车端兜底**：高德不可用 → 仅本地目的地（车道图直达），返回明确状态码
4. **无状态水平扩**：规划是 CPU 密集纯计算，按 QPS 扩副本；重规划请求（storm-cloud navigation 60s 超时语义）异步化走 RocketMQ

## 部署

无状态 gRPC 集群，8 副本起步；对高德出口流量统一走 NAT 网关（IP 白名单管理）。

## 降级

高德熔断 → 校内车道图模式；缓存命中失败 → 实时规划；整体不可用 → 任务创建侧拒单并给出明确错误码（复用 `navigation_request_failed`）。

## 验收

- 真实高德链路选点到参考路径 P95 < 2 s（契约不变）
- 缓存命中 P99 < 50 ms
- 熔断演练：高德断 5 min，校内目的地规划成功率 100%
