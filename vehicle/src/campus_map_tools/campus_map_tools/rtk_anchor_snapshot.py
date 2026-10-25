#!/usr/bin/env python3
"""② 锚点采集：停在控制点（≥6 个，四角+中心），静态采集 RTK 30s 取均值，
同时记录当时 SLAM 位姿 → (map_xy, wgs84) 锚点对，追加写入 anchors.json。

用法（W2 建图 SOP ②，见 docs/architecture.md §4）:
    ros2 run campus_map_tools rtk_anchor_snapshot --id gcp-01 --duration 30
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True, help='锚点 ID，如 gcp-01')
    parser.add_argument('--duration', type=float, default=30.0, help='RTK 静态采集时长（秒）')
    parser.add_argument('--anchors-json', default='anchors.json', help='输出锚点集文件')
    args = parser.parse_args()
    # TODO(N2): 订阅 /gps/fix（均值）+ /slam_toolbox/pose（当时位姿），
    #           RTK 状态非 fixed 时拒绝采集（gpsStatus != 4 直接报错退出）
    raise SystemExit(f'not implemented yet (W2): anchor={args.id} duration={args.duration}')


if __name__ == '__main__':
    main()
