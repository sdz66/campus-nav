#include "campus_coord/map_json.hpp"

namespace campus_coord {

// W1 交付：map.json 读写（nlohmann/json 或 RapidJSON），字段见 docs/architecture.md §2.2
std::optional<MapMeta> loadMapJson(const std::string& /*path*/) {
  // TODO(N1): 解析 datum/anchors/grid/problem_scenes/accuracy
  return std::nullopt;
}

bool saveMapJson(const std::string& /*path*/, const MapMeta& /*meta*/) {
  // TODO(N1)
  return false;
}

}  // namespace campus_coord
