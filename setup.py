#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='crownstone-ble',
    version="2.1.0",
    packages=find_packages(exclude=["examples","testing"]),
    author="Crownstone B.V.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crownstone/crownstone-lib-python-ble",
    install_requires=list(package.strip() for package in open('requirements.txt')),
    scripts=[
        'tools/cs_dfu_write_application',
        'tools/cs_scan_any_crownstone',
        'tools/cs_scan_for_alternative_state',
        'tools/cs_scan_known_crownstones',
        'tools/cs_switch_crownstone',
        'tools/cs_enable_microapp',
        'tools/cs_upload_microapp',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.7'
    ],
    python_requires='>=3.7',
)
