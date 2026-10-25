cmake_minimum_required(VERSION 3.8)
project(campus_localization)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(campus_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(pose_arbiter src/pose_arbiter.cpp)
ament_target_dependencies(pose_arbiter rclcpp campus_msgs geometry_msgs)
target_compile_features(pose_arbiter PUBLIC cxx_std_17)

install(TARGETS pose_arbiter DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
