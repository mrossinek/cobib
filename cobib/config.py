"""CoBib configuration module."""

from copy import deepcopy
import configparser
import io
import os
import sys

DEFAULTS = {
    'DATABASE': {
        'file': os.path.expanduser('~/.local/share/cobib/literature.yaml'),
        'open': 'xdg-open' if sys.platform.lower() == 'linux' else 'open',
        'grep': 'grep',
    },
    'FORMAT': {
        'month': 'int',
        'ignore_non_standard_types': False,
    },
    'TUI': {
        'prompt_before_quit': True,
        'reverse_order': True,
    },
    'KEY_BINDINGS': {
    },
    'COLORS': {
        'cursor_line_fg': 'white',
        'cursor_line_bg': 'cyan',
        'top_statusbar_fg': 'black',
        'top_statusbar_bg': 'yellow',
        'bottom_statusbar_fg': 'black',
        'bottom_statusbar_bg': 'yellow',
        'search_label_fg': 'blue',
        'search_label_bg': 'black',
        'search_query_fg': 'red',
        'search_query_bg': 'black',
    },
}


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
        # load default configuration
        ini_conf.read_dict(DEFAULTS)

        # read ini config file
        if configpath is not None:
            if isinstance(configpath, io.TextIOWrapper):
                configpath = configpath.name
            ini_conf.read(configpath)
        elif os.path.exists(os.path.expanduser('~/.config/cobib/config.ini')):
            ini_conf.read(os.path.expanduser('~/.config/cobib/config.ini'))

        # overwrite settings
        for section in ini_conf.sections():
            self.config[section] = deepcopy(ini_conf[section])

    # TODO config validation


CONFIG = Config()
