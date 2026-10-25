#!/usr/bin/env python3
"""定位误差评估：rosbag2 录制（RTK 真值 + /localization/pose）→ 逐项指标。

指标（docs/architecture.md §8）：
  横向误差 RMSE（RTK fixed 区 < 0.3 m；GNSS 退化区 < 0.5 m）
  位姿连续性（单帧跳变 < 0.2 m）
  定位可用率（非 LOST 占比 > 99%）
输出：PlotJuggler 可加载数据 + 指标报告（CI 门禁读 JSON）。
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bag', required=True, help='rosbag2 目录')
    parser.add_argument('--map-json', required=True, help='退化区 polygon 来源')
    parser.add_argument('--out', default='eval_report.json')
    args = parser.parse_args()
    # TODO(N5): mcap/SQLite3 读取 → 时间对齐（PTP 硬同步前提下按戳插值）→ 指标 → JSON
    raise SystemExit('not implemented yet (W12)')


if __name__ == '__main__':
    main()
