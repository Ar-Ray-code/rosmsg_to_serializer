cmake_minimum_required(VERSION 3.16)
project(rosmsg_to_serializer_example)

# set(CMAKE_C_COMPILER arm-none-eabi-gcc)
# set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --specs=nosys.specs")

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()


if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosmsg_to_serializer REQUIRED)

# Include -------------------------------
set(INCLUDE_DIRS
  ${CMAKE_CURRENT_BINARY_DIR}/generated
  ${std_msgs_INCLUDE_DIRS}
  ${geometry_msgs_INCLUDE_DIRS}
  ${sensor_msgs_INCLUDE_DIRS}
  ${builtin_interfaces_INCLUDE_DIRS}
)

custom_execute_command(
  std_msgs/msg/Bool
  std_msgs/msg/Header
  geometry_msgs/msg/Twist
  sensor_msgs/msg/Image
  builtin_interfaces/msg/Time
  geometry_msgs/msg/PoseStamped
)

# serialize_image_example ------------------
add_executable(serialize_image_example
  src/serialize_image_example.c
)

add_msg_serializer_dependency(serialize_image_example)

target_include_directories(serialize_image_example PUBLIC
  ${INCLUDE_DIRS}
)

# serialize_header_example ------------------
add_executable(serialize_header_example
  src/serialize_header_example.c
)
add_msg_serializer_dependency(serialize_header_example)
target_include_directories(serialize_header_example PUBLIC
  ${INCLUDE_DIRS}
)

# Install targets -------------------
install(TARGETS
  serialize_image_example
  serialize_header_example
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/generated/
        DESTINATION include/${PROJECT_NAME}/
        FILES_MATCHING PATTERN "*.h")

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()