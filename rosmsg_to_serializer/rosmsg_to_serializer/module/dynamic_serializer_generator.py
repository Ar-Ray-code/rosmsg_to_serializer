#!/usr/bin/env python3

import os
import sys
import json
import importlib
from typing import Dict, Any, List, Tuple, Optional, Union
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from .serializer_template import get_dynamic_serializer_template
from .deserializer_template import get_dynamic_deserializer_template


class DynamicMessageAnalyzer:
    def __init__(self):
        self.analyzed_types = {}
        self.builtin_types = {
            'boolean', 'bool', 'byte', 'char', 'float32', 'float64', 'double', 'float',
            'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 
            'int64', 'uint64', 'string', 'wstring'
        }
        
        self.c_type_mapping = {
            'boolean': 'bool',
            'bool': 'bool',
            'byte': 'uint8_t',
            'char': 'char',
            'float32': 'float',
            'float64': 'double',
            'double': 'double',
            'float': 'float',
            'int8': 'int8_t',
            'uint8': 'uint8_t',
            'int16': 'int16_t',
            'uint16': 'uint16_t',
            'int32': 'int32_t',
            'uint32': 'uint32_t',
            'int64': 'int64_t',
            'uint64': 'uint64_t',
            'string': 'rosidl_runtime_c__String',
            'wstring': 'rosidl_runtime_c__U16String'
        }
        
        self.type_sizes = {
            'bool': 1,
            'byte': 1,
            'char': 1,
            'float32': 4,
            'float64': 8,
            'double': 8,
            'float': 4,
            'int8': 1,
            'uint8': 1,
            'int16': 2,
            'uint16': 2,
            'int32': 4,
            'uint32': 4,
            'int64': 8,
            'uint64': 8
        }
    
    def analyze_message_type(self, message_type: str) -> Dict[str, Any]:
        if message_type in self.analyzed_types:
            return self.analyzed_types[message_type]
        
        parts = message_type.split('/')
        if len(parts) == 3 and parts[1] == 'msg':
            package_name, _, message_name = parts
        elif len(parts) == 2:
            # Handle format like "std_msgs/Header"
            package_name, message_name = parts
        else:
            raise ValueError(f"Invalid message type format: {message_type}")
        
        # Convert format to standard ROS2 format
        full_message_type = f"{package_name}/msg/{message_name}"
        
        try:
            package = importlib.import_module(f"{package_name}.msg")
            message_class = getattr(package, message_name)
            
            fields_and_types = message_class.get_fields_and_field_types()
            
            analyzed_message = {
                'package': package_name,
                'name': message_name,
                'full_name': full_message_type,
                'c_type': f"{package_name}__msg__{message_name}",
                'fields': []
            }
            
            for field_name, field_type in fields_and_types.items():
                field_info = self._analyze_field(field_name, field_type)
                analyzed_message['fields'].append(field_info)
            
            self.analyzed_types[full_message_type] = analyzed_message
            return analyzed_message
            
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not analyze message type {message_type}: {e}")
    
    def _analyze_field(self, field_name: str, field_type: str) -> Dict[str, Any]:
        field_info = {
            'name': field_name,
            'original_type': field_type,
            'is_builtin': False,
            'is_string': False,
            'is_array': False,
            'is_dynamic_array': False,
            'array_size': None,
            'base_type': None,
            'c_type': None,
            'nested_message': None,
            'size': None
        }
        
        if field_type.startswith('sequence<') and field_type.endswith('>'):
            field_info['is_dynamic_array'] = True
            field_info['is_array'] = True
            base_type = field_type[9:-1]  # remove "sequence<" and ">"
        elif field_type.endswith(']'):
            field_info['is_array'] = True
            bracket_start = field_type.find('[')
            base_type = field_type[:bracket_start]
            array_part = field_type[bracket_start+1:-1]
            
            if array_part == '':
                field_info['is_dynamic_array'] = True
            else:
                try:
                    field_info['array_size'] = int(array_part)
                except ValueError:
                    field_info['is_dynamic_array'] = True
        else:
            base_type = field_type
        
        field_info['base_type'] = base_type
        
        if (base_type in self.builtin_types or 
            base_type in ['double', 'float', 'int32', 'uint32', 'int64', 'uint64'] or
            base_type.startswith('uint') or base_type.startswith('int') or
            base_type in ['bool', 'byte', 'char']):
            field_info['is_builtin'] = True
            field_info['c_type'] = self.c_type_mapping.get(base_type, base_type)
            field_info['size'] = self.type_sizes.get(base_type)
            
            if base_type in ['string', 'wstring']:
                field_info['is_string'] = True
        else:
            if '/' in base_type and '/msg/' not in base_type:
                parts = base_type.split('/')
                if len(parts) == 2:
                    base_type = f"{parts[0]}/msg/{parts[1]}"
            
            field_info['nested_message'] = self.analyze_message_type(base_type)
            field_info['c_type'] = field_info['nested_message']['c_type']
        
        return field_info
    
    def get_all_dependencies(self, message_type: str) -> List[str]:
        dependencies = []
        analyzed = self.analyze_message_type(message_type)
        
        def collect_dependencies(msg_info):
            for field in msg_info['fields']:
                if field['nested_message']:
                    nested_type = field['nested_message']['full_name']
                    if nested_type not in dependencies:
                        dependencies.append(nested_type)
                        collect_dependencies(field['nested_message'])
        
        collect_dependencies(analyzed)
        return dependencies


class DynamicCodeGenerator:
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self.analyzer = DynamicMessageAnalyzer()
    
    def generate_serializer(self, message_type: str, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        analyzed_message = self.analyzer.analyze_message_type(message_type)
        dependencies = self.analyzer.get_all_dependencies(message_type)
        
        all_messages = {}
        for dep in dependencies:
            all_messages[dep] = self.analyzer.analyze_message_type(dep)
        all_messages[message_type] = analyzed_message
        
        self._generate_dynamic_serializer(analyzed_message, all_messages, output_path)
        self._generate_dynamic_deserializer(analyzed_message, all_messages, output_path)
    
    def _generate_dynamic_serializer(self, message: Dict[str, Any], all_messages: Dict[str, Any], output_path: Path):
        template_content = self._create_dynamic_serializer_template()
        template = self.env.from_string(template_content)
        
        content = template.render(
            message=message,
            all_messages=all_messages,
            analyzer=self.analyzer
        )
        
        msg_dir = output_path / message['package'] / message['name']
        msg_dir.mkdir(parents=True, exist_ok=True)
        
        with open(msg_dir / "serialize.h", "w") as f:
            f.write(content)
    
    def _generate_dynamic_deserializer(self, message: Dict[str, Any], all_messages: Dict[str, Any], output_path: Path):
        template_content = self._create_dynamic_deserializer_template()
        template = self.env.from_string(template_content)
        
        content = template.render(
            message=message,
            all_messages=all_messages,
            analyzer=self.analyzer
        )
        
        msg_dir = output_path / message['package'] / message['name']
        msg_dir.mkdir(parents=True, exist_ok=True)
        
        with open(msg_dir / "deserialize.h", "w") as f:
            f.write(content)
    
    def _create_dynamic_serializer_template(self) -> str:
        return get_dynamic_serializer_template()
    
    def _create_dynamic_deserializer_template(self) -> str:
        return get_dynamic_deserializer_template()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate dynamic serializer for ROS2 messages')
    parser.add_argument('message_type', help='Message type (e.g., geometry_msgs/msg/PoseStamped)')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    template_dir = script_dir / 'templates'
    
    template_dir.mkdir(exist_ok=True)
    
    try:
        generator = DynamicCodeGenerator(str(template_dir))
        generator.generate_serializer(args.message_type, args.output_dir)
        print(f"Serializer and deserializer for {args.message_type} generated successfully in {args.output_dir}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())