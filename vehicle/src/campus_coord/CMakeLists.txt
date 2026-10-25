cmake_minimum_required(VERSION 3.8)
project(campus_coord)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(GeographicLib REQUIRED)

add_library(${PROJECT_NAME} src/helmert.cpp src/map_json.cpp)
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_link_libraries(${PROJECT_NAME} PUBLIC ${GeographicLib_LIBRARIES})
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)

ament_export_targets(${PROJECT_NAME}Targets HAS_LIBRARY_TARGET)
ament_export_dependencies(GeographicLib)
ament_export_include_directories(include)

install(
  DIRECTORY include/
  DESTINATION include
)
install(
  TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}Targets
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_coord_chain test/test_coord_chain.cpp)
  target_link_libraries(test_coord_chain ${PROJECT_NAME})
  # 验收：已知控制点全链路往返闭合误差 < 0.1 m（G1 门）
endif()

ament_package()
