#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
from pathlib import Path
this_dir = Path(__file__).absolute().parent


if __name__ == "__main__":
    setup(use_scm_version={
        "write_to_template": '__version__ = "{version}"\n',
    })