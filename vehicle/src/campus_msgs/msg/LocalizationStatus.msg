# 定位状态（pose_arbiter 仲裁输出；状态机见 docs/architecture.md §5.2）
std_msgs/Header header
uint8 state
float32[3] covariance_diag   # x, y, yaw 协方差对角线
float32 rtk_hdop
string map_id
string map_version

uint8 NOMINAL=0
uint8 GNSS_DEGRADED=1
uint8 SCAN_LOST=2
uint8 DEAD_RECKONING=3
uint8 LOST=4
