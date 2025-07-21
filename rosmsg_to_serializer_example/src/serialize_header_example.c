#include <stdio.h>
#include "dynamic_serializer_integration.h"

#include <string.h>

#if !(defined(__x86_64__) && defined(__GNUC__))
__attribute__((weak)) int puts(const char *s) { (void)s; return 0; }
__attribute__((weak)) int printf(const char *fmt, ...) { (void)fmt; return 0; }
// #else
// #error "This code is intended for x86_64 architecture with GCC."
#endif

int serialize_header_example(void) {
    printf("--- 1. Serialization ---\n");
    std_msgs__msg__Header original_header;
    uint8_t serialized_buffer[256];
    
    char frame_id_data[] = "abcdefg";
    original_header.frame_id.data = frame_id_data;
    original_header.frame_id.size = strlen(frame_id_data);
    original_header.frame_id.capacity = sizeof(frame_id_data);
    original_header.stamp.sec = 10000;
    original_header.stamp.nanosec = 123456789;

    printf("Original Frame ID: '%s'\n", original_header.frame_id.data);
    printf("Original Timestamp: %d.%09u\n", original_header.stamp.sec, original_header.stamp.nanosec);
    
    size_t written_bytes = serialize_header_big_endian(&original_header, serialized_buffer, sizeof(serialized_buffer));
    
    if (written_bytes > 0)
    {
        printf("Serialized %lu bytes (hex): ", written_bytes);
        for(size_t i = 0; i < written_bytes; ++i) {
            printf("%02X ", serialized_buffer[i]);
        }
        printf("\n\n");
    } else {
        printf("Serialization failed.\n");
        return 1;
    }

    // --- 2. Deserialization ---
    printf("--- 2. Deserialization ---\n");
    std_msgs__msg__Header deserialized_header;
    
    printf("DEBUG: About to call deserialize_header_big_endian\n");
    printf("DEBUG: serialized_buffer first 20 bytes: ");
    for(size_t i = 0; i < 20 && i < written_bytes; ++i) {
        printf("%02X ", serialized_buffer[i]);
    }
    printf("\n");
    
    size_t read_bytes = deserialize_header_big_endian(
        serialized_buffer, 
        written_bytes, 
        &deserialized_header,
        256  // max_string_buffer_size
    );
    
    printf("DEBUG: deserialize_header_big_endian returned %zu\n", read_bytes);

    if (read_bytes > 0)
    {
        printf("Deserialized %lu bytes successfully.\n", read_bytes);
        printf("Deserialized Frame ID: '%s' (size: %zu)\n", 
               deserialized_header.frame_id.data,
               deserialized_header.frame_id.size);
        printf("Raw bytes: ");
        for(size_t i = 0; i < deserialized_header.frame_id.size + 1; ++i) {
            printf("%02X ", (unsigned char)deserialized_header.frame_id.data[i]);
        }
        printf("\n");
        printf("Deserialized Timestamp: %d.%09u\n", deserialized_header.stamp.sec, deserialized_header.stamp.nanosec);
        
        // --- 3. 検証 ---
        printf("\n--- 3. Verification ---\n");
        if (original_header.stamp.sec == deserialized_header.stamp.sec &&
            original_header.stamp.nanosec == deserialized_header.stamp.nanosec &&
            original_header.frame_id.size == deserialized_header.frame_id.size)
        {
            printf("SUCCESS: Deserialized data matches original data.\n");
            printf("Original Frame ID: '%s', Deserialized Frame ID: '%s'\n",
                     original_header.frame_id.data,
                     deserialized_header.frame_id.data);

            printf("Original Timestamp: %d.%09u, Deserialized Timestamp: %d.%09u\n",
                        original_header.stamp.sec,
                        original_header.stamp.nanosec,
                        deserialized_header.stamp.sec,
                        deserialized_header.stamp.nanosec);

            
        } else {
            printf("FAILURE: Data mismatch!\n");
        }

    } else {
        printf("Deserialization failed.\n");
        return 1;
    }
    return 0;
}

int main(void)
{
    printf("Running serialize_header_example...\n");
    int result = serialize_header_example();
    if (result != 0) {
        printf("serialize_header_example failed with error code: %d\n", result);
    } else {
        printf("serialize_header_example completed successfully.\n");
    }
    printf("\n");
    return 0;  // Return success
}
