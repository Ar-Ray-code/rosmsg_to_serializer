cmake_minimum_required(VERSION 3.16)
project(rosmsg_to_serializer)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

find_package(ament_cmake_python REQUIRED)

# Install Python package
ament_python_install_package(rosmsg_to_serializer)

# Install Python executables to both lib and bin directories
install(PROGRAMS
  rosmsg_to_serializer/rosmsg_to_serializer.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME rosmsg_to_serializer
)

# Also install to bin for PATH access
install(PROGRAMS
  rosmsg_to_serializer/rosmsg_to_serializer.py
  DESTINATION bin
  RENAME rosmsg_to_serializer
)

# Install CMake files
install(
  FILES
    cmake/rosmsg_to_serializer.cmake
    cmake/rosmsg_to_serializerConfig.cmake
    cmake/rosmsg_to_serializerConfig-version.cmake
  DESTINATION share/${PROJECT_NAME}/cmake
)

# Set PYTHONPATH so the module can be found during build
set(ENV{PYTHONPATH} "${CMAKE_CURRENT_SOURCE_DIR}:$ENV{PYTHONPATH}")

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# Export the package and CMake files
ament_export_dependencies()

# Export the CMake configuration to include our CMake files
ament_package(
  CONFIG_EXTRAS cmake/rosmsg_to_serializer.cmake
)