#!/usr/bin/env python3

import os
import sys
import json
from typing import Dict, Any, List, Set
from pathlib import Path
from .dynamic_serializer_generator import DynamicMessageAnalyzer


class DynamicTypeGenerator:
    def __init__(self):
        self.analyzer = DynamicMessageAnalyzer()
        self.generated_types = set()
        self.type_definitions = []
    
    def generate_type_definitions(self, message_types: List[str], output_dir: str):
        output_path = Path(output_dir)
        common_dir = output_path / 'common'
        common_dir.mkdir(parents=True, exist_ok=True)
        
        all_types = set()
        for msg_type in message_types:
            all_types.add(msg_type)
            dependencies = self.analyzer.get_all_dependencies(msg_type)
            all_types.update(dependencies)
        
        sorted_types = self._sort_by_dependencies(all_types)
        
        self._generate_dynamic_types_header(sorted_types, common_dir)
        self._generate_serialize_utils(common_dir)
    
    def _sort_by_dependencies(self, types: Set[str]) -> List[str]:
        sorted_types = []
        processed = set()
        
        def process_type(type_name: str):
            if type_name in processed:
                return
            
            analyzed = self.analyzer.analyze_message_type(type_name)
            
            for field in analyzed['fields']:
                if field['nested_message']:
                    nested_type = field['nested_message']['full_name']
                    if nested_type in types and nested_type not in processed:
                        process_type(nested_type)
            
            sorted_types.append(type_name)
            processed.add(type_name)
        
        for type_name in types:
            process_type(type_name)
        
        return sorted_types
    
    def _generate_dynamic_types_header(self, sorted_types: List[str], output_dir: Path):
        header_content = '''#ifndef MSG_SERIALIZER_DYNAMIC_TYPES_H_
#define MSG_SERIALIZER_DYNAMIC_TYPES_H_

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

'''
        header_content += '\n// Include necessary headers for message types\n'
        for type_name in sorted_types:
            type_names = type_name.split('/')
            msg_type_str = f"#include <"
            if len(type_names) > 1:
                msg_type_str += '/'.join(type_names[:-1]) + '/'
                for i in range(len(type_names[-1])):
                    if type_names[-1][i].isupper() and i != 0:
                        msg_type_str += '_' + type_names[-1][i].lower()
                    else:
                        msg_type_str += type_names[-1][i].lower()
                msg_type_str += '.h>\n'
            else:
                msg_type_str += type_names[0].lower() + '.h>\n'
            header_content += msg_type_str
        
        
        header_content += '#endif // MSG_SERIALIZER_DYNAMIC_TYPES_H_\n'
        
        with open(output_dir / 'dynamic_types.h', 'w') as f:
            f.write(header_content)
    
    def _generate_struct_definition(self, analyzed: Dict[str, Any]) -> str:
        content = f"// {analyzed['full_name']}\n"
        content += f"typedef struct {analyzed['c_type']} {{\n"
        
        for field in analyzed['fields']:
            content += self._generate_field_definition(field)
        
        content += f"}} {analyzed['c_type']};\n"
        
        return content
    
    def _generate_field_definition(self, field: Dict[str, Any]) -> str:
        field_type = field['c_type']
        field_name = field['name']
        
        if field['is_string']:
            return f"    {field_type} {field_name};\n"
        elif field['is_dynamic_array']:
            return f"    struct {{\n        {field_type}* data;\n        size_t size;\n        size_t capacity;\n    }} {field_name};\n"
        elif field['is_array']:
            return f"    {field_type} {field_name}[{field['array_size']}];\n"
        else:
            return f"    {field_type} {field_name};\n"
    
    def _generate_serialize_utils(self, output_dir: Path):
        utils_content = '''#ifndef MSG_SERIALIZER_UTILS_H_
#define MSG_SERIALIZER_UTILS_H_

#include <stddef.h>
#include <stdint.h>

static inline void virt_memcpy(uint8_t* dest, const uint8_t* src, size_t n)
{
    for (size_t i = 0; i < n; ++i) {
        dest[i] = src[i];
    }
}

static inline void serialize_u32_be(uint8_t* buffer, uint32_t value)
{
    buffer[0] = (uint8_t)((value >> 24) & 0xFF);
    buffer[1] = (uint8_t)((value >> 16) & 0xFF);
    buffer[2] = (uint8_t)((value >> 8) & 0xFF);
    buffer[3] = (uint8_t)(value & 0xFF);
}

static inline uint32_t deserialize_u32_be(const uint8_t* buffer)
{
    return ((uint32_t)buffer[0] << 24) |
           ((uint32_t)buffer[1] << 16) |
           ((uint32_t)buffer[2] << 8)  |
           ((uint32_t)buffer[3]);
}

static inline void serialize_u16_be(uint8_t* buffer, uint16_t value)
{
    buffer[0] = (uint8_t)((value >> 8) & 0xFF);
    buffer[1] = (uint8_t)(value & 0xFF);
}

static inline uint16_t deserialize_u16_be(const uint8_t* buffer)
{
    return ((uint16_t)buffer[0] << 8) |
           ((uint16_t)buffer[1]);
}

static inline void serialize_u64_be(uint8_t* buffer, uint64_t value)
{
    buffer[0] = (uint8_t)((value >> 56) & 0xFF);
    buffer[1] = (uint8_t)((value >> 48) & 0xFF);
    buffer[2] = (uint8_t)((value >> 40) & 0xFF);
    buffer[3] = (uint8_t)((value >> 32) & 0xFF);
    buffer[4] = (uint8_t)((value >> 24) & 0xFF);
    buffer[5] = (uint8_t)((value >> 16) & 0xFF);
    buffer[6] = (uint8_t)((value >> 8) & 0xFF);
    buffer[7] = (uint8_t)(value & 0xFF);
}

static inline uint64_t deserialize_u64_be(const uint8_t* buffer)
{
    return ((uint64_t)buffer[0] << 56) |
           ((uint64_t)buffer[1] << 48) |
           ((uint64_t)buffer[2] << 40) |
           ((uint64_t)buffer[3] << 32) |
           ((uint64_t)buffer[4] << 24) |
           ((uint64_t)buffer[5] << 16) |
           ((uint64_t)buffer[6] << 8)  |
           ((uint64_t)buffer[7]);
}

#endif // MSG_SERIALIZER_UTILS_H_
'''
        
        with open(output_dir / 'serialize_utils.h', 'w') as f:
            f.write(utils_content)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate dynamic type definitions for ROS2 messages')
    parser.add_argument('message_types', nargs='+', help='Message types (e.g., geometry_msgs/msg/PoseStamped)')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    try:
        generator = DynamicTypeGenerator()
        generator.generate_type_definitions(args.message_types, args.output_dir)
        print(f"Successfully generated dynamic type definitions for: {', '.join(args.message_types)}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())