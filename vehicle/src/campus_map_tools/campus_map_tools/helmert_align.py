#!/usr/bin/env python3
"""③ Helmert 对齐：读取 anchors.json，最小二乘解算 map→ENU，
残差 RMSE < 0.15 m 验收（G2 门），结果写回 map.json（datum.heading_deg + anchors + accuracy）。

用法:
    python3 -m campus_map_tools.helmert_align --anchors anchors.json --out maps/campus-v1/map.json
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--anchors', required=True)
    parser.add_argument('--out', required=True, help='目标 map.json 路径')
    args = parser.parse_args()
    # TODO(N2): 与 campus_coord 的 solveHelmert 同一算法的 Python 版（pyproj + numpy），
    #           打印逐点残差表；RMSE >= 0.15 时以非零码退出，禁止写回
    raise SystemExit('not implemented yet (W2)')


if __name__ == '__main__':
    main()
