# tools/

离线工具（不依赖 ROS 运行时）：

- `eval_localization.py` — 定位误差评估（G3/G5 门验收工具）
- `plotjuggler/` — PlotJuggler 四联图配置模板（定位误差 / AMCL 得分 / RTK 状态 / EKF 协方差）
- `sim_regression/` — 仿真回归门禁（5 条固定路线 + 3 个退化场景，CI 调用）
