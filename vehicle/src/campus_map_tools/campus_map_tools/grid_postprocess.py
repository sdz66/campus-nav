#!/usr/bin/env python3
"""⑤ 出图：SLAM 点云 → 2D 栅格投影 → 飞点剔除/墙体补全辅助 → map.pgm + map.yaml。

用法:
    python3 -m campus_map_tools.grid_postprocess --cloud map_cloud.pcd --resolution 0.05
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cloud', required=True)
    parser.add_argument('--resolution', type=float, default=0.05)
    args = parser.parse_args()
    # TODO(N2): SLAM Toolbox 输出 + 人工修图（去飞点/补墙）后生成 nav2 map_server 可加载的
    #           map.pgm/map.yaml，并初始化同目录 map.json（datum 暂空，锚点对齐后回填）
    raise SystemExit('not implemented yet (W2)')


if __name__ == '__main__':
    main()
