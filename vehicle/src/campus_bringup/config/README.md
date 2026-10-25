# campus_bringup 配置

车端与仿真两套参数的覆盖层（launch 里以优先级叠在包参数之上）。

- `vehicle.yaml` — 实车覆盖（W3 外参标定后回填）
- `simulation.yaml` — 仿真覆盖（use_sim_time、噪声参数）
