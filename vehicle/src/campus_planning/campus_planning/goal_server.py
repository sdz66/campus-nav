#!/usr/bin/env python3
"""goal_server：接收任务系统/APP 的 GCJ-02 目标点 → 校验可达性 → Nav2 goal。

降级语义：高德不可用时仅接受校内目的地（车道图/POI 直达）并给出明确状态。
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-json', required=True)
    args = parser.parse_args()
    # TODO(N4): service 化（/planning/set_goal），对接 storm-cloud 任务下发 navigationData
    raise SystemExit('not implemented yet (W9)')


if __name__ == '__main__':
    main()
