# 地图资产（maps/）

每个版本一个目录，三件套齐套才允许进主干：

```
maps/campus-v1/
├── map.pgm      # 占用栅格（nav2 map_server 可加载）
├── map.yaml     # 栅格元数据（origin/resolution）
└── map.json     # datum / anchors / problem_scenes / accuracy（见 docs/architecture.md §2.2）
```

## 版本规则

- 命名 `campus-vN`，与云端 `maps/upload` 的版本一致（storm-cloud 平台同款约定）
- **二进制（pgm）走 Git LFS**：`git lfs track "*.pgm"`
- 锚点 RMSE < 0.15 m 才能发布（G2 门）；发布后版本不可变（改图出新版本）
- 重建图触发条件：校园施工、长期 SLAM 漂移、新增退化区

## 上传云端

```bash
# 建图 SOP ⑥ 完成后，走 storm-cloud 平台
POST /console-api/storm/v3/maps/upload         # 三件套打包
POST /console-api/storm/v3/maps/publish        # 发布 + 下发车辆
```
