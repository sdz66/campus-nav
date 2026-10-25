#pragma once

/**
 * @file map_json.hpp
 * @brief map.json 读写——datum/锚点/退化区/精度的单一事实来源（docs/architecture.md §2.2）
 */
#include <array>
#include <optional>
#include <string>
#include <vector>

namespace campus_coord {

struct Wgs84 {
  double lat{0.0};
  double lon{0.0};
  double alt{0.0};
};

struct Anchor {
  std::string id;
  Wgs84 wgs84;
  std::array<double, 2> map_xy{0.0, 0.0};
  double residual_m{0.0};
  std::string collected_at;
};

struct ProblemScene {
  std::string id;                 // 如 scene-wutong
  std::string type;               // gnss_denied / narrow / tunnel
  std::vector<std::array<double, 2>> polygon_map_xy;
  std::string note;
};

struct MapMeta {
  std::string map_id;
  std::string version;
  Wgs84 datum;                    // ENU 原点（navsat_transform 的 datum 参数）
  double heading_deg{0.0};        // 基准朝向
  std::vector<Anchor> anchors;
  double anchor_rmse_m{0.0};
  std::vector<ProblemScene> problem_scenes;
};

std::optional<MapMeta> loadMapJson(const std::string& path);
bool saveMapJson(const std::string& path, const MapMeta& meta);

}  // namespace campus_coord
