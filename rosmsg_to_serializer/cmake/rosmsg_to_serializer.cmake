# rosmsg_to_serializer CMake plugin
# Provides custom_execute_command function for generating ROS2 message serializers

# Find Python3 for running the generator
find_package(Python3 REQUIRED COMPONENTS Interpreter)

# Main function to execute message serializer generation
function(custom_execute_command)
    set(messages ${ARGV})
    
    if(NOT messages)
        message(FATAL_ERROR "custom_execute_command: No messages specified")
    endif()
    
    # Set output directory for generated files
    set(SERIALIZER_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
    file(MAKE_DIRECTORY "${SERIALIZER_OUTPUT_DIR}")
    
    # Set PYTHONPATH to include the rosmsg_to_serializer package source directory
    set(rosmsg_to_serializer_PYTHON_PATH "${CMAKE_CURRENT_LIST_DIR}/..")
    
    # Create custom target for serializer generation
    add_custom_target(generate_msg_serializers
        COMMAND ${CMAKE_COMMAND} -E env "PYTHONPATH=${rosmsg_to_serializer_PYTHON_PATH}:$ENV{PYTHONPATH}" 
                ${Python3_EXECUTABLE} -m rosmsg_to_serializer.rosmsg_to_serializer
                --output-dir "${SERIALIZER_OUTPUT_DIR}"
                --messages ${messages}
        COMMENT "Generating serializers for messages: ${messages}"
        VERBATIM
    )
    
    # Add include directory for generated headers
    include_directories("${SERIALIZER_OUTPUT_DIR}")
    
    # Make this target available globally
    set_property(GLOBAL PROPERTY MSG_SERIALIZER_TARGET generate_msg_serializers)
    set_property(GLOBAL PROPERTY MSG_SERIALIZER_OUTPUT_DIR "${SERIALIZER_OUTPUT_DIR}")
    
    message(STATUS "rosmsg_to_serializer: Configured for messages: ${messages}")
    message(STATUS "rosmsg_to_serializer: Output directory: ${SERIALIZER_OUTPUT_DIR}")
endfunction()

# Helper function to add dependencies on the serializer generation
function(add_msg_serializer_dependency target_name)
    get_property(serializer_target GLOBAL PROPERTY MSG_SERIALIZER_TARGET)
    if(serializer_target)
        add_dependencies(${target_name} ${serializer_target})
    endif()
endfunction()

# Export the functions
set(rosmsg_to_serializer_FOUND TRUE)