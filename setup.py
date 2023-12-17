#!/usr/bin/env python3
# ruff: noqa: D100

import os

import setuptools

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, "requirements.txt"), "r") as f:
    REQUIREMENTS = f.read().strip().split("\n")

setuptools.setup(install_requires=REQUIREMENTS)
