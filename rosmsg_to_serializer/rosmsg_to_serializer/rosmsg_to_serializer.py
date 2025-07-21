#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path

from .module.dynamic_serializer_generator import DynamicCodeGenerator
from .module.dynamic_type_generator import DynamicTypeGenerator


def main():
    parser = argparse.ArgumentParser(description='Generate C/C++ serializers and deserializers from ROS2 message definitions dynamically')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--messages', nargs='*')
    
    args = parser.parse_args()
    
    default_messages = [
        'geometry_msgs/msg/Twist',
        'geometry_msgs/msg/PoseStamped',
        'geometry_msgs/msg/PoseWithCovarianceStamped'
    ]
    
    messages = args.messages if args.messages else default_messages
    
    output_dir = Path(args.output_dir)
    
    for msg in messages:
        print(f"  - {msg}")
    
    try:
        type_generator = DynamicTypeGenerator()
        type_generator.generate_type_definitions(messages, str(output_dir))
        
        template_dir = Path(__file__).parent / 'templates'
        template_dir.mkdir(exist_ok=True)
        
        serializer_generator = DynamicCodeGenerator(str(template_dir))
        
        for msg_type in messages:
            try:
                serializer_generator.generate_serializer(msg_type, str(output_dir))
                print(f"  ✅ {msg_type}")
            except Exception as e:
                print(f"  ❌ {msg_type}: {e}")
        
        print("3: generate_integration_headers")
        generate_integration_headers(output_dir, messages)
        print("Generated integration headers successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def generate_integration_headers(output_dir: Path, messages: list):
    integration_header = '''#ifndef DYNAMIC_SERIALIZER_INTEGRATION_H_
#define DYNAMIC_SERIALIZER_INTEGRATION_H_

#include "common/dynamic_types.h"
#include "common/serialize_utils.h"

'''
    
    for msg_type in messages:
        parts = msg_type.split('/')
        if len(parts) >= 3:
            package_name = parts[0]
            message_name = parts[2]
            
            integration_header += f'#include "{package_name}/{message_name}/serialize.h"\n'
            integration_header += f'#include "{package_name}/{message_name}/deserialize.h"\n'
    
    integration_header += '''
#endif // DYNAMIC_SERIALIZER_INTEGRATION_H_
'''
    
    with open(output_dir / 'dynamic_serializer_integration.h', 'w') as f:
        f.write(integration_header)


if __name__ == '__main__':
    sys.exit(main())