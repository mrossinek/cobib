"""CoBib configuration module."""

from copy import deepcopy
import configparser
import io
import logging
import os
import sys

LOGGER = logging.getLogger(__name__)

ANSI_COLORS = [
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'white',
]

DEFAULTS = {
    'DATABASE': {
        'file': os.path.expanduser('~/.local/share/cobib/literature.yaml'),
        'open': 'xdg-open' if sys.platform.lower() == 'linux' else 'open',
        'grep': 'grep',
        'search_ignore_case': False,
    },
    'FORMAT': {
        'month': 'int',
        'ignore_non_standard_types': False,
        'default_entry_type': 'article',
    },
    'TUI': {
        'default_list_args': '-l',
        'prompt_before_quit': True,
        'reverse_order': True,
        'scroll_offset': 3,
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
        'popup_help_fg': 'white',
        'popup_help_bg': 'green',
        'popup_stdout_fg': 'white',
        'popup_stdout_bg': 'blue',
        'popup_stderr_fg': 'white',
        'popup_stderr_bg': 'red',
        'selection_fg': 'white',
        'selection_bg': 'magenta',
    },
}

XDG_CONFIG_FILE = '~/.config/cobib/config.ini'


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
            LOGGER.info('Loading configuration from %s', configpath)
            ini_conf.read(configpath)
        elif os.path.exists(os.path.expanduser(XDG_CONFIG_FILE)):
            LOGGER.info('Loading configuration from default location: %s',
                        os.path.expanduser(XDG_CONFIG_FILE))
            ini_conf.read(os.path.expanduser(XDG_CONFIG_FILE))

        # overwrite settings
        for section in ini_conf.sections():
            self.config[section] = deepcopy(ini_conf[section])

    def validate(self):
        """Validates the configuration at runtime."""
        LOGGER.info('Validating the runtime configuration.')

        # DATABASE section
        LOGGER.debug('Validing the DATABASE configuration section.')
        self._assert(self.config.get('DATABASE', None) is not None,
                     "Missing DATABASE section.")
        self._assert(isinstance(self.config.get('DATABASE', {}).get('file', None), str),
                     "DATABASE/file should be a string.")
        self._assert(isinstance(self.config.get('DATABASE', {}).get('open', None), str),
                     "DATABASE/open should be a string.")
        self._assert(isinstance(self.config.get('DATABASE', {}).get('grep', None), str),
                     "DATABASE/grep should be a string.")
        self._assert(isinstance(
            self.config.get('DATABASE', {}).getboolean('search_ignore_case', None), bool),
                     "DATABASE/search_ignore_case should be a boolean.")

        # FORMAT section
        LOGGER.debug('Validing the FORMAT configuration section.')
        self._assert(self.config.get('FORMAT', None) is not None,
                     "Missing FORMAT section.")
        self._assert(self.config.get('FORMAT', {}).get('month', None) in ('int', 'str'),
                     "FORMAT/month should be either 'int' or 'str'.")
        self._assert(isinstance(
            self.config.get('FORMAT', {}).getboolean('ignore_non_standard_types', None), bool),
                     "FORMAT/ignore_non_standard_types should be a boolean.")
        self._assert(isinstance(self.config.get('FORMAT', {}).get('default_entry_type', None), str),
                     "FORMAT/default_entry_type should be a string.")

        # TUI section
        LOGGER.debug('Validing the TUI configuration section.')
        self._assert(self.config.get('TUI', None) is not None,
                     "Missing TUI section.")
        self._assert(isinstance(self.config.get('TUI', {}).get('default_list_args', None), str),
                     "TUI/default_list_args should be a string.")
        self._assert(isinstance(
            self.config.get('TUI', {}).getboolean('prompt_before_quit', None), bool),
                     "TUI/prompt_before_quit should be a boolean.")
        self._assert(isinstance(
            self.config.get('TUI', {}).getboolean('reverse_order', None), bool),
                     "TUI/reverse_order should be a boolean.")
        self._assert(isinstance(
            self.config.get('TUI', {}).getint('scroll_offset', None), int),
                     "TUI/scroll_offset should be an integer.")

        # KEY_BINDINGS section
        LOGGER.debug('Validing the KEY_BINDINGS configuration section.')
        self._assert(self.config.get('KEY_BINDINGS', None) is not None,
                     "Missing KEY_BINDINGS section.")
        # actual key bindings are asserted when mapped by the TUI instance

        # COLORS section
        LOGGER.debug('Validing the COLORS configuration section.')
        self._assert(self.config.get('COLORS', None) is not None,
                     "Missing COLORS section.")
        for name in DEFAULTS['COLORS']:
            self._assert(name in self.config.get('COLORS', {}).keys(),
                         f"Missing value for COLORS/{name}")
        available_colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')
        for name, color in self.config.get('COLORS', {}).items():
            if name not in DEFAULTS['COLORS'] and name not in available_colors:
                LOGGER.warning('Ignoring unknown TUI color: %s', name)
            self._assert(color in available_colors or
                         (len(color.strip('#')) == 6 and
                          tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4))),
                         f"Unknown color specification: {color}")

    @staticmethod
    def _assert(expression, error):
        """Asserts the expression is True.

        Raises:
            RuntimeError with the specified error string.
        """
        if not expression:
            raise RuntimeError(error)

    def get_ansi_color(self, name):
        """Returns an ANSI color code for the named color.

        Args:
            name (str): a named color as specified in the configuration *excluding* the `_fg` or
                        `_bg` suffix.

        Returns:
            A string representing the foreground and background ANSI color code.
        """
        fg_color = 30 + ANSI_COLORS.index(self.config['COLORS'].get(name + '_fg'))
        bg_color = 40 + ANSI_COLORS.index(self.config['COLORS'].get(name + '_bg'))

        return f'\x1b[{fg_color};{bg_color}m'


CONFIG = Config()
