#include <stdio.h>
#include "dynamic_serializer_integration.h"

#include <string.h>

#if !(defined(__x86_64__) && defined(__GNUC__))
__attribute__((weak)) int puts(const char *s) { (void)s; return 0; }
__attribute__((weak)) int printf(const char *fmt, ...) { (void)fmt; return 0; }
// #else
// #error "This code is intended for x86_64 architecture with GCC."
#endif

int serialize_image_example(void) {
    uint8_t image_8x8[64] = {
        0, 1, 2, 3, 4, 5, 6, 7,
        8, 9, 10, 11, 12, 13, 14, 15,
        16, 17, 18, 19, 20, 21, 22, 23,
        24, 25, 26, 27, 28, 29, 30, 31,
        32, 33, 34, 35, 36, 37, 38, 39,
        40, 41, 42, 43, 44, 45, 46, 47,
        48, 49, 50, 51, 52, 53, 54, 55,
        56, 57, 58, 59, 60, 61, 62, 63
    };

    printf("--- 1. Serialization ---\n");
    sensor_msgs__msg__Image original_image;
    
    // Initialize header
    char frame_id_data[] = "camera_link";
    original_image.header.frame_id.data = frame_id_data;
    original_image.header.frame_id.size = strlen(frame_id_data);
    original_image.header.frame_id.capacity = sizeof(frame_id_data);
    original_image.header.stamp.sec = 1000;
    original_image.header.stamp.nanosec = 123456789;
    
    // Initialize image data
    original_image.height = 8;
    original_image.width = 8;
    original_image.encoding.data = "mono8";
    original_image.encoding.size = strlen("mono8");
    original_image.encoding.capacity = strlen("mono8") + 1;
    original_image.is_bigendian = 0;
    original_image.step = 8; // 8 pixels per row
    original_image.data.data = image_8x8;
    original_image.data.size = sizeof(image_8x8);
    original_image.data.capacity = sizeof(image_8x8);

    uint8_t serialized_buffer[256];
    size_t written_bytes = serialize_image_big_endian(&original_image, serialized_buffer, sizeof(serialized_buffer));

    if (written_bytes > 0) {
        printf("Serialized %zu bytes (hex): ", written_bytes);
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
    sensor_msgs__msg__Image deserialized_image;
    // sensor_msgs__msg__Image__init(&deserialized_image);
    size_t read_bytes = deserialize_image_big_endian(
        serialized_buffer, 
        written_bytes, 
        &deserialized_image,
        256  // max_string_buffer_size
    );

    if (read_bytes > 0) {
        printf("Deserialized %lu bytes successfully.\n", read_bytes);
        printf("Deserialized Image: %dx%d, Encoding: '%s', Step: %u\n",
               deserialized_image.height,
               deserialized_image.width,
               deserialized_image.encoding.data,
               deserialized_image.step);
        printf("Header Frame ID: '%s'\n", 
               deserialized_image.header.frame_id.data);
        
        // --- 3. Verification ---
        printf("\n--- 3. Verification ---\n");
        if (original_image.height == deserialized_image.height &&
            original_image.width == deserialized_image.width &&
            original_image.encoding.size == deserialized_image.encoding.size &&
            original_image.step == deserialized_image.step)
        {
            printf("SUCCESS: Deserialized data matches original data.\n");
            printf("Original Encoding: '%s', Deserialized Encoding: '%s'\n",
                        original_image.encoding.data,
                        deserialized_image.encoding.data);
                        
            printf("Original Dimensions: %dx%d, Deserialized Dimensions: %dx%d\n",
                        original_image.height,
                        original_image.width,
                        deserialized_image.height,
                        deserialized_image.width);

            printf("Original Data Size: %zu, Deserialized Data Size: %zu\n",
                        original_image.data.size,
                        deserialized_image.data.size);
            printf("Original Data: ");
            for (size_t i = 0; i < original_image.data.size; ++i) {
                printf("%02X ", original_image.data.data[i]);
            }
            printf("\nDeserialized Data: ");
            for (size_t i = 0; i < deserialized_image.data.size; ++i) {
                printf("%02X ", deserialized_image.data.data[i]);
            }
            printf("\n");

            // Compare the actual pixel data
            if (memcmp(original_image.data.data, deserialized_image.data.data, original_image.data.size) == 0) {
                printf("SUCCESS: Pixel data matches.\n");
            } else {
                printf("FAILURE: Pixel data mismatch!\n");
            }
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
    printf("Running serialize_image_example...\n");
    int result = serialize_image_example();
    if (result != 0) {
        printf("serialize_image_example failed with error code: %d\n", result);
    } else {
        printf("serialize_image_example completed successfully.\n");
    }
    printf("\n");
}
