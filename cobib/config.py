"""CoBib configuration module."""

from copy import deepcopy
import configparser
import io
import os


class Config:
    """Class used solely for the global configuration object."""

    def __init__(self):
        """Initializes the configuration data dictionary."""
        self.config = {}

    def set_config(self, configpath=None):
        """Sets the configuration.

        If a configuration file is provided as a keyword argument it is used instead of the default
        paths. The configparser module is used to parse the INI configuration file.

        Args:
            configpath (str or io.TextIOWrapper, optional): the path to an optional configuration
                                                            file.
        """
        ini_conf = configparser.ConfigParser()
        ini_conf.optionxform = str  # makes option names case-sensitive!

        # read ini config file
        if configpath is not None:
            if isinstance(configpath, io.TextIOWrapper):
                configpath = configpath.name
            ini_conf.read(configpath)
        elif os.path.exists(os.path.expanduser('~/.config/cobib/config.ini')):
            ini_conf.read(os.path.expanduser('~/.config/cobib/config.ini'))
        else:
            root = os.path.abspath(os.path.dirname(__file__))
            ini_conf.read(os.path.join(root, 'docs', 'default.ini'))

        # copy sections into dictionary
        for section in ini_conf.sections():
            self.config[section] = deepcopy(ini_conf[section])

    # TODO config validation


CONFIG = Config()
