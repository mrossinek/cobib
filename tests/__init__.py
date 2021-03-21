"""CoBib's test suite."""

import os

from .cmdline_test import CmdLineTest


def get_resource(filename, path=None):
    """Gets the absolute path of the filename."""
    root = os.path.dirname(__file__)
    path = root if path is None else os.path.join(root, path)
    return os.path.abspath(os.path.join(path, filename))
