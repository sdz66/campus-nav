# C3 地图服务（map-service）

> 设计文档；代码目录 [cloud/map-service/](../../cloud/map-service/)。上游契约：storm-cloud `maps/*`（19 条，契约不变）。

## 职责边界

**做**：地图资产生命周期（上传/版本/发布/可见性）、venue 文件存储与分发、围栏规则发布。
**不做**：地图生成（车端建图管道）、栅格渲染（车端本地）。

## 接口

REST（复用 storm-cloud 信封契约）+ 事件：

| 接口 | 说明 |
| --- | --- |
| `maps/upload` / `maps/publish` / `maps/list` 等 19 条 | 契约见 storm-cloud `07-地图与路线.md`，原样演进 |
| `GET /internal/maps/{id}/{version}/manifest` | 车端增量同步：文件哈希清单 |
| `GET /internal/maps/.../{file}?sig=` | CDN 回源签名 URL（15 min） |
| Kafka `map.meta.v1`（compacted） | 版本发布/可见性变更事件 |

## 数据模型

```
PostgreSQL（全局单元）：maps / map_visibilities / route_templates
OSS：oss://storm-maps/{city}/{map_id}/{version}/(map.pgm|yaml|json|tiles/)
Redis：map:published:{city} 版本指针缓存
```

版本规则：锚点 RMSE < 0.15 m 才允许 publish；发布后版本不可变；废弃版本 30 天转低频存储。

## 关键设计

1. **上传直传 OSS**：服务端只签名（STS），不代理大文件流量
2. **增量分发**：车端按 manifest 哈希 diff 拉差异分片（分片 4MB，断点续传）
3. **围栏规则管道**：problem_scenes 变更 → 写 `fence.rules.v1`（compacted）→ Flink broadcast 热更新——规则变更到车端/云端生效 < 10 s
4. **可见性**：多组织共享全量覆盖语义（storm-cloud 已实现），发布事件按可见组织广播

## 部署

全局单元部署（地图元数据强一致）；文件流量全部走 OSS/CDN，服务本身轻量 4 副本。

## 降级

CDN 故障 → OSS 直连签名（兜底路径恒可用）；OSS 故障 → 车端继续用本地缓存版本（地图是只读资产，天然容忍）。

## 验收

- 500MB 地图上传直传成功率 > 99.9%，断点续传可用
- 版本发布 → 围栏规则在 Flink 侧生效 < 10 s
- 契约测试：19 条接口与 storm-cloud openapi 全量对齐
