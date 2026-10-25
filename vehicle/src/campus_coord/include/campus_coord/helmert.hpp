#pragma once

/**
 * @file helmert.hpp
 * @brief Helmert 相似变换（平移 + 旋转 + 缩放）——建图期 map 系 → ENU 系对齐
 *
 * 最小二乘解算：输入 ≥6 个锚点对 (map_xy, enu_xy)，输出变换参数与残差 RMSE。
 * 验收门 G2：残差 RMSE < 0.15 m（见 docs/architecture.md §8）。
 */
#include <array>
#include <optional>
#include <vector>

namespace campus_coord {

struct AnchorPair {
  std::array<double, 2> map_xy;  // 栅格地图系坐标（米）
  std::array<double, 2> enu_xy;  // ENU 坐标（米，datum 起算）
};

struct HelmertResult {
  double tx{0.0};       // 平移 x（米）
  double ty{0.0};       // 平移 y
  double theta{0.0};    // 旋转角（rad，map → ENU）
  double scale{1.0};    // 缩放（理想 ≈ 1，偏离大说明 SLAM 尺度漂移）
  double rmse{0.0};     // 残差 RMSE（米）
};

/// 最小二乘解算 Helmert 参数（锚点数 >= 2；>= 6 时残差统计才有意义）
std::optional<HelmertResult> solveHelmert(const std::vector<AnchorPair>& anchors);

/// 应用变换：map_xy -> enu_xy
std::array<double, 2> applyHelmert(const HelmertResult& h, const std::array<double, 2>& map_xy);

}  // namespace campus_coord
