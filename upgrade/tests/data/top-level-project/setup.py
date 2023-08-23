#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
from pathlib import Path

this_dir = Path(__file__).absolute().parent

version = Path(this_dir, "VERSION").read_text().strip()

if __name__ == "__main__":
    setup(
        install_requires=[
            f"oll-dependency1=={version}",
            f"oll-dependency2=={version}",
        ],
        data_files=[
            (
                "lib/site-packages/oll_test_top_level",
                ["./README.md", "./constraints.txt"],
            )
        ],
    )
