"""CoBib configuration module"""

from copy import deepcopy
import configparser
import io
import os


class Config:  # pylint: disable=too-few-public-methods
    """Global configuration class"""
    def __init__(self):
        # initialize dictionary
        self.config = {}

    def set_config(self, configpath=None):
        """Set config"""
        ini_conf = configparser.ConfigParser()
        ini_conf.optionxform = str  # makes option names case-sensitive!

        # read ini config file
        if configpath is not None:
            if isinstance(configpath, io.TextIOWrapper):
                configpath = configpath.name
            ini_conf.read(configpath)
        elif os.path.exists('~/.config/cobib/config.ini'):
            ini_conf.read(os.path.expanduser('~/.config/cobib/config.ini'))
        else:
            root = os.path.abspath(os.path.dirname(__file__))
            ini_conf.read(os.path.join(root, 'docs', 'default.ini'))

        # copy sections into dictionary
        for section in ini_conf.sections():
            self.config[section] = deepcopy(ini_conf[section])

    # TODO config validation


CONFIG = Config()
