#include "campus_coord/helmert.hpp"

#include <cmath>

namespace campus_coord {

// W1 交付：最小二乘解算（经典 4 参数相似变换，见测绘学标准做法）
std::optional<HelmertResult> solveHelmert(const std::vector<AnchorPair>& anchors) {
  if (anchors.size() < 2) return std::nullopt;
  // TODO(N1): 按 docs/architecture.md §2.3 实现最小二乘：
  //   [a -b; b a] * map_xy + [tx ty] = enu_xy, a = s*cosθ, b = s*sinθ
  //   对 a,b,tx,ty 建立法方程求解，theta = atan2(b, a), scale = hypot(a, b)
  return HelmertResult{};
}

std::array<double, 2> applyHelmert(const HelmertResult& h, const std::array<double, 2>& map_xy) {
  const double c = h.scale * std::cos(h.theta);
  const double s = h.scale * std::sin(h.theta);
  return {c * map_xy[0] - s * map_xy[1] + h.tx,
          s * map_xy[0] + c * map_xy[1] + h.ty};
}

}  // namespace campus_coord
