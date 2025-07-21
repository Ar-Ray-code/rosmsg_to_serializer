#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = "Dynamic serializer system for ROS2 messages using CMake integration."

setup(
    name="rosmsg_to_serializer",
    version="0.0.0",
    description="Generate C/C++ serializers and deserializers from ROS2 message definitions dynamically.",
    long_description="A tool to dynamically generate C/C++ struct serializers and deserializers from ROS2 message types using Jinja2 templates and CMake integration.",
    long_description_content_type="text/markdown",
    author="Ar-Ray-code",
    author_email="ray255ar@gmail.com",
    url="https://github.com/Ar-Ray-code/rosmsg_to_serializer",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'rosmsg_to_serializer': [
            'templates/*.j2',
            'templates/*.h.j2',
        ],
    },
    install_requires=[
        "jinja2>=3.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'rosmsg_to_serializer=rosmsg_to_serializer.rosmsg_to_serializer:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Utilities",
    ],
)