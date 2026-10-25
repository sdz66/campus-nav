/**
 * @file pose_arbiter.cpp
 * @brief 定位降级仲裁（自研核心之一，状态机见 docs/architecture.md §5.2）
 *
 * 输入：ekf_global 位姿、AMCL 得分、RTK 状态（gpsStatus/hdop）、map.json 退化区 polygon
 * 输出：/localization/status（campus_msgs/LocalizationStatus）
 * 策略：NOMINAL → GNSS_DEGRADED → SCAN_LOST → DEAD_RECKONING → LOST
 */
#include "rclcpp/rclcpp.hpp"
#include "campus_msgs/msg/localization_status.hpp"
#include "geometry_msgs/msg/pose_with_covariance_stamped.hpp"
#include "sensor_msgs/msg/nav_sat_fix.hpp"

namespace campus_localization {

class PoseArbiter : public rclcpp::Node {
 public:
  PoseArbiter() : Node("pose_arbiter") {
    // 参数：退化区 polygon（来自 map.json）、AMCL 得分阈值与滑动窗口、
    //       RTK 门控（gpsStatus==4 && hdop < 2）、各状态超时
    // TODO(N3):
    //   1. 订阅 /ekf_global/pose、/amcl_score、/gps/fix、map.json（problem_scenes）
    //   2. 状态机迁移 + 原因日志
    //   3. DEGRADED 时对 ekf_global 的 GPS 量测权重置零（重配 fuse_gps 参数或重映射输入）
    //   4. LOST 事件 → 发布到安全层 + 云端告警（storm-cloud nodes/location 上报）
    status_pub_ = create_publisher<campus_msgs::msg::LocalizationStatus>(
        "/localization/status", 10);
  }

 private:
  rclcpp::Publisher<campus_msgs::msg::LocalizationStatus>::SharedPtr status_pub_;
};

}  // namespace campus_localization

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<campus_localization::PoseArbiter>());
  rclcpp::shutdown();
  return 0;
}
