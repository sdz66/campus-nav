# map.json 的运行时投影（建图/下发/降级判定共用，见 docs/architecture.md §2.2）
string map_id
string version
float64[3] datum_wgs84       # lat, lon, alt
float64 heading_deg          # 基准朝向（map 系与 ENU 的夹角）
string venue_file_path
string[] problem_scene_ids
