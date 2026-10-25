#!/usr/bin/env python3
"""高德路径规划客户端（M1 最高优先级风险 M1：高德无校内路网！）。

分层策略（docs/architecture.md §6.1）：
  外部路段（校门→楼栋）  高德 API，GCJ-02 折线
  校内路段               自建车道图（map.json internal_routes），W3 前定方案

用法:
    ros2 run campus_planning amap_client --from 118.6080,31.8639 --to 118.6120,31.8660
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from', dest='src', required=True, help='GCJ-02 "lng,lat"')
    parser.add_argument('--to', dest='dst', required=True, help='GCJ-02 "lng,lat"')
    parser.add_argument('--mock', action='store_true', help='mock 模式（CI 用，不打真接口）')
    args = parser.parse_args()
    # TODO(N4):
    #   1. 高德官方 API（key 走环境变量 AMAP_KEY，限流重试）
    #   2. mock 模式返回固定折线（CI 断言转换链路，不依赖外网）
    #   3. API 不可用降级：仅校内目的地（栅格级直达）+ 明确状态
    raise SystemExit('not implemented yet (W8)')


if __name__ == '__main__':
    main()
