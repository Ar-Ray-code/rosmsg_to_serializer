#!/usr/bin/env python3

def get_dynamic_serializer_template() -> str:
    return '''#ifndef SERIALIZE_{{ message.name.upper() }}_H_
#define SERIALIZE_{{ message.name.upper() }}_H_

#include <stddef.h>
#include <stdint.h>
#include "common/serialize_utils.h"

{%- for msg_type, msg_info in all_messages.items() %}
// Forward declaration for serializer of {{ msg_type }}
static size_t serialize_{{ message.c_type.lower() }}_{{ msg_info.name.lower() }}_fields(const {{ msg_info.c_type }}* msg, uint8_t* buffer, size_t buffer_size, size_t offset);
{%- endfor %}

{%- macro serialize_field_dynamic(field, var_name, buffer_name, offset_name) %}
{%- if field.is_string %}
    // String field: {{ field.name }}
    const uint32_t {{ field.name }}_len = {{ var_name }}->{{ field.name }}.size;
    const uint32_t {{ field.name }}_len_with_null = {{ field.name }}_len + 1;
    
    if ({{ offset_name }} + sizeof(uint32_t) + {{ field.name }}_len_with_null > buffer_size) {
        return 0;
    }
    
    serialize_u32_be({{ buffer_name }} + {{ offset_name }}, {{ field.name }}_len_with_null);
    {{ offset_name }} += sizeof(uint32_t);
    
    virt_memcpy({{ buffer_name }} + {{ offset_name }}, (const uint8_t*){{ var_name }}->{{ field.name }}.data, {{ field.name }}_len);
    {{ buffer_name }}[{{ offset_name }} + {{ field.name }}_len] = '\\0';
    {{ offset_name }} += {{ field.name }}_len_with_null;
{%- elif field.is_dynamic_array %}
    // Dynamic array field: {{ field.name }}
    const uint32_t {{ field.name }}_size = {{ var_name }}->{{ field.name }}.size;
    
    if ({{ offset_name }} + sizeof(uint32_t) > buffer_size) {
        return 0;
    }
    
    serialize_u32_be({{ buffer_name }} + {{ offset_name }}, {{ field.name }}_size);
    {{ offset_name }} += sizeof(uint32_t);
    
    for (uint32_t i = 0; i < {{ field.name }}_size; ++i) {
        {%- if field.is_builtin %}
        {%- if field.size == 1 %}
        if ({{ offset_name }} + 1 > buffer_size) return 0;
        {{ buffer_name }}[{{ offset_name }}] = {{ var_name }}->{{ field.name }}.data[i];
        {{ offset_name }} += 1;
        {%- elif field.size == 2 %}
        if ({{ offset_name }} + 2 > buffer_size) return 0;
        serialize_u16_be({{ buffer_name }} + {{ offset_name }}, {{ var_name }}->{{ field.name }}.data[i]);
        {{ offset_name }} += 2;
        {%- elif field.size == 4 %}
        if ({{ offset_name }} + 4 > buffer_size) return 0;
        serialize_u32_be({{ buffer_name }} + {{ offset_name }}, *(uint32_t*)&{{ var_name }}->{{ field.name }}.data[i]);
        {{ offset_name }} += 4;
        {%- elif field.size == 8 %}
        if ({{ offset_name }} + 8 > buffer_size) return 0;
        serialize_u64_be({{ buffer_name }} + {{ offset_name }}, *(uint64_t*)&{{ var_name }}->{{ field.name }}.data[i]);
        {{ offset_name }} += 8;
        {%- endif %}
        {%- else %}
        // Nested message in array: {{ field.nested_message.name }}
        size_t {{ field.name }}_nested_result = serialize_{{ message.c_type.lower() }}_{{ field.nested_message.name.lower() }}_fields(&{{ var_name }}->{{ field.name }}.data[i], {{ buffer_name }}, buffer_size, {{ offset_name }});
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
        {{ buffer_name }}[{{ offset_name }}] = {{ var_name }}->{{ field.name }}[i];
        {{ offset_name }} += 1;
    }
    {%- elif field.size == 2 %}
    if ({{ offset_name }} + {{ field.array_size * 2 }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        serialize_u16_be({{ buffer_name }} + {{ offset_name }}, {{ var_name }}->{{ field.name }}[i]);
        {{ offset_name }} += 2;
    }
    {%- elif field.size == 4 %}
    if ({{ offset_name }} + {{ field.array_size * 4 }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        serialize_u32_be({{ buffer_name }} + {{ offset_name }}, *(uint32_t*)&{{ var_name }}->{{ field.name }}[i]);
        {{ offset_name }} += 4;
    }
    {%- elif field.size == 8 %}
    if ({{ offset_name }} + {{ field.array_size * 8 }} > buffer_size) return 0;
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        serialize_u64_be({{ buffer_name }} + {{ offset_name }}, *(uint64_t*)&{{ var_name }}->{{ field.name }}[i]);
        {{ offset_name }} += 8;
    }
    {%- endif %}
    {%- else %}
    // Nested message array: {{ field.nested_message.name }}
    for (int i = 0; i < {{ field.array_size }}; ++i) {
        size_t {{ field.name }}_nested_result = serialize_{{ message.c_type.lower() }}_{{ field.nested_message.name.lower() }}_fields(&{{ var_name }}->{{ field.name }}[i], {{ buffer_name }}, buffer_size, {{ offset_name }});
        if ({{ field.name }}_nested_result == 0) return 0;
        {{ offset_name }} = {{ field.name }}_nested_result;
    }
    {%- endif %}
{%- else %}
    // Scalar field: {{ field.name }}
    {%- if field.is_builtin %}
    {%- if field.size == 1 %}
    if ({{ offset_name }} + 1 > buffer_size) return 0;
    {{ buffer_name }}[{{ offset_name }}] = {{ var_name }}->{{ field.name }};
    {{ offset_name }} += 1;
    {%- elif field.size == 2 %}
    if ({{ offset_name }} + 2 > buffer_size) return 0;
    serialize_u16_be({{ buffer_name }} + {{ offset_name }}, {{ var_name }}->{{ field.name }});
    {{ offset_name }} += 2;
    {%- elif field.size == 4 %}
    if ({{ offset_name }} + 4 > buffer_size) return 0;
    serialize_u32_be({{ buffer_name }} + {{ offset_name }}, *(uint32_t*)&{{ var_name }}->{{ field.name }});
    {{ offset_name }} += 4;
    {%- elif field.size == 8 %}
    if ({{ offset_name }} + 8 > buffer_size) return 0;
    serialize_u64_be({{ buffer_name }} + {{ offset_name }}, *(uint64_t*)&{{ var_name }}->{{ field.name }});
    {{ offset_name }} += 8;
    {%- endif %}
    {%- else %}
    // Nested message: {{ field.nested_message.name }}
    size_t {{ field.name }}_nested_result = serialize_{{ message.c_type.lower() }}_{{ field.nested_message.name.lower() }}_fields(&{{ var_name }}->{{ field.name }}, {{ buffer_name }}, buffer_size, {{ offset_name }});
    if ({{ field.name }}_nested_result == 0) return 0;
    {{ offset_name }} = {{ field.name }}_nested_result;
    {%- endif %}
{%- endif %}
{%- endmacro %}

{%- for msg_type, msg_info in all_messages.items() %}
// Serializer for {{ msg_type }}
static size_t serialize_{{ message.c_type.lower() }}_{{ msg_info.name.lower() }}_fields(const {{ msg_info.c_type }}* msg, uint8_t* buffer, size_t buffer_size, size_t offset)
{
    (void)buffer_size;  // Unused in this context, but can be used for buffer size checks
    if (msg == NULL || buffer == NULL) {
        return 0;
    }
    
{%- for field in msg_info.fields %}
    {{ serialize_field_dynamic(field, "msg", "buffer", "offset") }}
{%- endfor %}
    
    return offset;
}
{%- endfor %}

// Main serializer function
size_t serialize_{{ message.name.lower() }}_big_endian(const {{ message.c_type }}* msg, uint8_t* buffer, size_t buffer_size)
{
    return serialize_{{ message.c_type.lower() }}_{{ message.name.lower() }}_fields(msg, buffer, buffer_size, 0);
}

#endif // SERIALIZE_{{ message.name.upper() }}_H_
'''