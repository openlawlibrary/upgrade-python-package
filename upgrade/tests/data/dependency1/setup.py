#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
from pathlib import Path
this_dir = Path(__file__).absolute().parent


if __name__ == "__main__":
    setup(
        data_files=[
            ('lib/site-packages/oll',
            ['./README.md', './constraints.txt'])
        ],
    )
