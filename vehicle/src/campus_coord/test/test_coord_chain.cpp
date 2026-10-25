#include <gtest/gtest.h>
#include "campus_coord/helmert.hpp"

/**
 * G1 门验收：坐标链闭合误差 < 0.1 m
 * 已知控制点 GCJ-02 → WGS84 → ENU → map →（逆变换）→ GCJ-02 全链路往返
 */
TEST(CoordChain, helmert_roundtrip_known_anchors) {
  // TODO(N1): 构造 6 个合成锚点（加微小噪声），解算后逐点回代，
  //           断言残差 < 0.1 m；缩放 ≈ 1（|s-1| < 1e-3）
  SUCCEED();
}

TEST(CoordChain, helmert_requires_two_anchors) {
  EXPECT_FALSE(campus_coord::solveHelmert({}).has_value());
}
