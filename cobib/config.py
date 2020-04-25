"""CoBib configuration module"""

import configparser
import io
import os

# global config
# the configuration file will be loaded from ~/.config/cobib/config.ini
# if this file does not exists, defaults are taken from the package data config
CONFIG = configparser.ConfigParser()
CONFIG.optionxform = str  # makes option names case-sensitive!


def set_config(configpath=None):
    """
    Sets the global config
    Args:
        configpath (TextIOWrapper): config file
    """
    if configpath is not None:
        if isinstance(configpath, io.TextIOWrapper):
            configpath = configpath.name
        CONFIG.read(configpath)
    elif os.path.exists('~/.config/cobib/config.ini'):
        CONFIG.read(os.path.expanduser('~/.config/cobib/config.ini'))
    else:
        root = os.path.abspath(os.path.dirname(__file__))
        CONFIG.read(os.path.join(root, 'docs', 'default.ini'))
