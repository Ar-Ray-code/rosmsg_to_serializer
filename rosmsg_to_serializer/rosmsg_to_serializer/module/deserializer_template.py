#!/usr/bin/env python3

def get_dynamic_deserializer_template() -> str:
    return '''#ifndef DESERIALIZE_{{ message.name.upper() }}_H_
#define DESERIALIZE_{{ message.name.upper() }}_H_
// TEMPLATE_MARKER: UPDATED_TEMPLATE_V2

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include "common/serialize_utils.h"

{%- for msg_type, msg_info in all_messages.items() %}
// Forward declaration for deserializer of {{ msg_type }}
static size_t deserialize_{{ message.c_type.lower() }}_{{ msg_info.name.lower() }}_fields(const uint8_t* buffer, size_t buffer_size, size_t offset, {{ msg_info.c_type }}* msg, char* string_buffer, size_t string_buffer_size);
{%- endfor %}

{%- macro deserialize_field_dynamic(field, var_name, buffer_name, offset_name) %}
{%- if field.is_string %}
    // String field: {{ field.name }}
    if ({{ offset_name }} + sizeof(uint32_t) > buffer_size) return 0;
    
    uint32_t {{ field.name }}_len_with_null = deserialize_u32_be({{ buffer_name }} + {{ offset_name }});
    {{ offset_name }} += sizeof(uint32_t);
    
    if ({{ offset_name }} + {{ field.name }}_len_with_null > buffer_size) return 0;
    
    // Allocate individual memory for this string field
    char* {{ field.name }}_string_buffer = (char*)malloc({{ field.name }}_len_with_null);
    if ({{ field.name }}_string_buffer == NULL) {
        return 0; // Memory allocation failed
    }
    
    virt_memcpy((uint8_t*){{ field.name }}_string_buffer, {{ buffer_name }} + {{ offset_name }}, {{ field.name }}_len_with_null);
    {{ var_name }}->{{ field.name }}.data = {{ field.name }}_string_buffer;
    {{ var_name }}->{{ field.name }}.size = {{ field.name }}_len_with_null - 1;
    {{ var_name }}->{{ field.name }}.capacity = {{ field.name }}_len_with_null;
    {{ offset_name }} += {{ field.name }}_len_with_null;
{%- elif field.is_dynamic_array %}
    // Dynamic array field: {{ field.name }}
    if ({{ offset_name }} + sizeof(uint32_t) > buffer_size) return 0;
    
    uint32_t {{ field.name }}_size = deserialize_u32_be({{ buffer_name }} + {{ offset_name }});
    {{ offset_name }} += sizeof(uint32_t);
    
    // Allocate memory for dynamic array elements
    {{ var_name }}->{{ field.name }}.size = {{ field.name }}_size;
    {{ var_name }}->{{ field.name }}.capacity = {{ field.name }}_size;
    if ({{ field.name }}_size > 0) {
        {{ var_name }}->{{ field.name }}.data = ({{ field.c_type }}*)malloc({{ field.name }}_size * sizeof({{ field.c_type }}));
        if ({{ var_name }}->{{ field.name }}.data == NULL) {
            return 0; // Memory allocation failed
        }
    } else {
        {{ var_name }}->{{ field.name }}.data = NULL;
    }
    
    for (uint32_t i = 0; i < {{ field.name }}_size; ++i) {
        {%- if field.is_builtin %}
        {%- if field.size == 1 %}
        if ({{ offset_name }} + 1 > buffer_size) return 0;
        {{ var_name }}->{{ field.name }}.data[i] = {{ buffer_name }}[{{ offset_name }}];
        {{ offset_name }} += 1;
        {%- elif field.size == 2 %}
        if ({{ offset_name }} + 2 > buffer_size) return 0;
        {{ var_name }}->{{ field.name }}.data[i] = deserialize_u16_be({{ buffer_name }} + {{ offset_name }});
        {{ offset_name }} += 2;
        {%- elif field.size == 4 %}
        if ({{ offset_name }} + 4 > buffer_size) return 0;
        *(uint32_t*)&{{ var_name }}->{{ field.name }}.data[i] = deserialize_u32_be({{ buffer_name }} + {{ offset_name }});
        {{ offset_name }} += 4;
        {%- elif field.size == 8 %}
        if ({{ offset_name }} + 8 > buffer_size) return 0;
        *(uint64_t*)&{{ var_name }}->{{ field.name }}.data[i] = deserialize_u64_be({{ buffer_name }} + {{ offset_name }});
        {{ offset_name }} += 8;
        {%- endif %}
        {%- else %}
        // Nested message in array: {{ field.nested_message.name }}
        size_t {{ field.name }}_nested_result = deserialize_{{ message.c_type.lower() }}_{{ field.nested_message.name.lower() }}_fields({{ buffer_name }}, buffer_size, {{ offset_name }}, &{{ var_name }}->{{ field.name }}.data[i], string_buffer, string_buffer_size);
        if ({{ field.name }}_nested_result == 0) return 0;
        {{ offset_name }} = {{ field.name }}_nested_result;
        {%- endif %}
    }
{%- elif field.is_array %}
    // Fixed array field: {{ field.name }}
    {%- if field.is_builtin %}
    {%- if field.size == 1 %}
    if ({{ offset_name }} + {{ field.array_size }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        {{ var_name }}->{{ field.name }}[i] = {{ buffer_name }}[{{ offset_name }}];
        {{ offset_name }} += 1;
    }
    {%- elif field.size == 2 %}
    if ({{ offset_name }} + {{ field.array_size * 2 }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        {{ var_name }}->{{ field.name }}[i] = deserialize_u16_be({{ buffer_name }} + {{ offset_name }});
        {{ offset_name }} += 2;
    }
    {%- elif field.size == 4 %}
    if ({{ offset_name }} + {{ field.array_size * 4 }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        *(uint32_t*)&{{ var_name }}->{{ field.name }}[i] = deserialize_u32_be({{ buffer_name }} + {{ offset_name }});
        {{ offset_name }} += 4;
    }
    {%- elif field.size == 8 %}
    if ({{ offset_name }} + {{ field.array_size * 8 }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        *(uint64_t*)&{{ var_name }}->{{ field.name }}[i] = deserialize_u64_be({{ buffer_name }} + {{ offset_name }});
        {{ offset_name }} += 8;
    }
    {%- endif %}
    {%- else %}
    // Nested message array: {{ field.nested_message.name }}
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        size_t {{ field.name }}_nested_result = deserialize_{{ message.c_type.lower() }}_{{ field.nested_message.name.lower() }}_fields({{ buffer_name }}, buffer_size, {{ offset_name }}, &{{ var_name }}->{{ field.name }}[i], string_buffer, string_buffer_size);
        if ({{ field.name }}_nested_result == 0) return 0;
        {{ offset_name }} = {{ field.name }}_nested_result;
    }
    {%- endif %}
{%- else %}
    // Scalar field: {{ field.name }}
    {%- if field.is_builtin %}
    {%- if field.size == 1 %}
    if ({{ offset_name }} + 1 > buffer_size) return 0;
    {{ var_name }}->{{ field.name }} = {{ buffer_name }}[{{ offset_name }}];
    {{ offset_name }} += 1;
    {%- elif field.size == 2 %}
    if ({{ offset_name }} + 2 > buffer_size) return 0;
    {{ var_name }}->{{ field.name }} = deserialize_u16_be({{ buffer_name }} + {{ offset_name }});
    {{ offset_name }} += 2;
    {%- elif field.size == 4 %}
    if ({{ offset_name }} + 4 > buffer_size) return 0;
    *(uint32_t*)&{{ var_name }}->{{ field.name }} = deserialize_u32_be({{ buffer_name }} + {{ offset_name }});
    {{ offset_name }} += 4;
    {%- elif field.size == 8 %}
    if ({{ offset_name }} + 8 > buffer_size) return 0;
    *(uint64_t*)&{{ var_name }}->{{ field.name }} = deserialize_u64_be({{ buffer_name }} + {{ offset_name }});
    {{ offset_name }} += 8;
    {%- endif %}
    {%- else %}
    // Nested message: {{ field.nested_message.name }}
    size_t {{ field.name }}_nested_result = deserialize_{{ message.c_type.lower() }}_{{ field.nested_message.name.lower() }}_fields({{ buffer_name }}, buffer_size, {{ offset_name }}, &{{ var_name }}->{{ field.name }}, string_buffer, string_buffer_size);
    if ({{ field.name }}_nested_result == 0) return 0;
    {{ offset_name }} = {{ field.name }}_nested_result;
    {%- endif %}
{%- endif %}
{%- endmacro %}

{%- for msg_type, msg_info in all_messages.items() %}
// Deserializer for {{ msg_type }}
static size_t deserialize_{{ message.c_type.lower() }}_{{ msg_info.name.lower() }}_fields(const uint8_t* buffer, size_t buffer_size, size_t offset, {{ msg_info.c_type }}* msg, char* string_buffer, size_t string_buffer_size)
{
    (void)string_buffer;  // Unused in this context, but can be used for string fields
    (void)string_buffer_size;  // Unused in this context, but can be used for string fields
    (void)buffer_size;  // Unused in this context, but can be used for buffer size checks
    if (msg == NULL || buffer == NULL) {
        return 0;
    }
    
{%- for field in msg_info.fields %}
    {{ deserialize_field_dynamic(field, "msg", "buffer", "offset") }}
{%- endfor %}
    
    return offset;
}
{%- endfor %}

// Main deserializer function
// Note: String fields allocate individual memory blocks that must be freed by the caller
size_t deserialize_{{ message.name.lower() }}_big_endian(const uint8_t* buffer, size_t buffer_size, {{ message.c_type }}* msg, size_t max_string_buffer_size)
{
    (void)max_string_buffer_size; // Not used with individual string allocation
    // Pass NULL for string_buffer since we allocate individually for each string
    size_t result = deserialize_{{ message.c_type.lower() }}_{{ message.name.lower() }}_fields(buffer, buffer_size, 0, msg, NULL, 0);
    return result;
}

#endif // DESERIALIZE_{{ message.name.upper() }}_H_
'''