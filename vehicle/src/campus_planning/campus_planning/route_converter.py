#!/usr/bin/env python3
"""路径转换：GCJ-02 折线 → WGS84（高德 API/公开算法）→ ENU（pyproj，datum=map.json）→ map 系。

转换带来源标记（source: amap_api | public_algo）与残差，禁止 GCJ-02 进入系统内部传播。
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--polyline', required=True, help='GCJ-02 折线 "lng,lat;lng,lat;..."')
    parser.add_argument('--map-json', required=True, help='datum 来源（campus_coord 库同构）')
    args = parser.parse_args()
    # TODO(N4): 与 campus_coord C++ 库同一转换链的 Python 版（pyproj），
    #           输出 nav_msgs/Path（/global_reference_path）+ 转换报告
    raise SystemExit('not implemented yet (W8)')


if __name__ == '__main__':
    main()
