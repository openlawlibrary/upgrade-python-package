#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
from pathlib import Path

this_dir = Path(__file__).absolute().parent

version = Path(this_dir, 'VERSION').read_text().strip()

if __name__ == "__main__":
    setup(
        install_requires=[
            f"oll-dependency1=={version}",
            f"oll-dependency2=={version}",
            'defusedxml'
        ],
        data_files=[("lib/site-packages/oll", ["./README.md", "./constraints.txt"])],
    )
