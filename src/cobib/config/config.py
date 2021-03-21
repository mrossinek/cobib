"""coBib's configuration."""

import configparser
import copy
import importlib.util
import io
import logging
import os
import sys

LOGGER = logging.getLogger(__name__)

ANSI_COLORS = [
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]


class Config(dict):
    """coBib's configuration object.

    The configuration has undergone a major revision during v3.0 when it was redesigned from loading
    a `INI` file with the `configparser` module to become a standalone Python object.
    This class wraps the `dict` type and exposes the dictionary keys as attributes to ease access
    (for both, getting and setting).
    Furthermore, nested attributes can be set directly without having to ensure that the parent
    attribute is already present.

    Source: https://stackoverflow.com/a/3031270
    """

    XDG_CONFIG_FILE = "~/.config/cobib/config.py"
    # TODO: remove legacy configuration support on 1.1.2022
    LEGACY_XDG_CONFIG_FILE = "~/.config/cobib/config.ini"

    DEFAULTS = {
        "logging": {
            "logfile": os.path.expanduser("~/.cache/cobib/cobib.log"),
        },
        "commands": {
            "edit": {
                "default_entry_type": "article",
                "editor": os.environ.get("EDITOR", "vim"),
            },
            "open": {
                "command": "xdg-open" if sys.platform.lower() == "linux" else "open",
            },
            "search": {"grep": "grep", "ignore_case": False},
        },
        "database": {
            "file": os.path.expanduser("~/.local/share/cobib/literature.yaml"),
            "format": {
                "month": int,
                "suppress_latex_warnings": True,
            },
            "git": False,
        },
        "parsers": {
            "bibtex": {
                "ignore_non_standard_types": False,
            },
        },
        "tui": {
            "default_list_args": ["-l"],
            "prompt_before_quit": True,
            "reverse_order": True,
            "scroll_offset": 3,
            "colors": {
                "cursor_line_fg": "white",
                "cursor_line_bg": "cyan",
                "top_statusbar_fg": "black",
                "top_statusbar_bg": "yellow",
                "bottom_statusbar_fg": "black",
                "bottom_statusbar_bg": "yellow",
                "search_label_fg": "blue",
                "search_label_bg": "black",
                "search_query_fg": "red",
                "search_query_bg": "black",
                "popup_help_fg": "white",
                "popup_help_bg": "green",
                "popup_stdout_fg": "white",
                "popup_stdout_bg": "blue",
                "popup_stderr_fg": "white",
                "popup_stderr_bg": "red",
                "selection_fg": "white",
                "selection_bg": "magenta",
            },
            "key_bindings": {
                "prompt": ":",
                "search": "/",
                "help": "?",
                "add": "a",
                "delete": "d",
                "edit": "e",
                "filter": "f",
                "modify": "m",
                "open": "o",
                "quit": "q",
                "redo": "r",
                "sort": "s",
                "undo": "u",
                "select": "v",
                "wrap": "w",
                "export": "x",
                "show": "ENTER",
            },
        },
    }

    # pylint: disable=super-init-not-called
    def __init__(self, value=None):
        """Initializer of the recursive, attribute-access, dict-like configuration object.

        The initializer does nothing when `None` is given.
        When a dict is given, all values are set as attributes.

        Args:
            value (dict, optional): a dictionary of settings.
        """
        if value is None:
            pass
        elif isinstance(value, dict):
            for key, val in value.items():
                self.__setitem__(key, val)
        else:
            raise TypeError("expected dict")

    def __setitem__(self, key, value):
        """Sets a key, value pair in the object's dictionary.

        Args:
            key (str): the attributes' name.
            value (Any): the attributes' value.
        """
        if isinstance(value, dict) and not isinstance(value, Config):
            value = Config(value)
        super().__setitem__(key, value)

    def __setattr__(self, key, value):
        """Use __setitem__ to set attributes unless it is a private (`__`) field.

        This is necessary in order to avoid a RecursionError during the pdoc generation.

        Args:
            key (str): the attributes' name.
            value (Any): the attributes' value.
        """
        if key[0:2] == "__":
            super().__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    # A helper object for detecting the nested recursion-threshold.
    MARKER = object()

    def __getitem__(self, key):
        """Gets a key from the configuration object's dictionary.

        If the key is not present yet, it is automagically initialized with an empty configuration
        object to allow recursive attribute-setting.

        Args:
            key (str): the queried attributes' name.
        """
        found = self.get(key, Config.MARKER)
        if found is Config.MARKER:
            found = Config()
            super().__setitem__(key, found)
        return found

    def __getattr__(self, key):
        """Use __getitem__ to get attributes unless it is a private (`__`) field.

        This is necessary in order to avoid a RecursionError during the pdoc generation.

        Args:
            key (str): the queried attributes' name.
        """
        if key[0:2] == "__":
            return self.get(key)
        return self.__getitem__(key)

    def update(self, **kwargs):
        """Updates the configuration with a dictionary of settings.

        This ensures values are deepcopied, too.
        """
        for key, value in kwargs.items():
            self[key] = copy.deepcopy(value)

    @staticmethod
    def load(configpath=None):
        """Loads another configuration object at runtime.

        WARNING: The new Python-like configuration allows essentially arbitrary Python code so it is
        the user's responsibility to treat this with care!

        Args:
            configpath (str, io.TextIOWrapper): the path to the configuration.
        """
        if configpath is not None:
            if isinstance(configpath, io.TextIOWrapper):
                configpath = configpath.name
            LOGGER.info("Loading configuration from %s", configpath)
        elif os.path.exists(os.path.expanduser(Config.XDG_CONFIG_FILE)):
            LOGGER.info(
                "Loading configuration from default location: %s",
                os.path.expanduser(Config.XDG_CONFIG_FILE),
            )
            configpath = os.path.expanduser(Config.XDG_CONFIG_FILE)
        elif os.path.exists(os.path.expanduser(Config.LEGACY_XDG_CONFIG_FILE)):
            LOGGER.info(
                "Loading configuration from default location: %s",
                os.path.expanduser(Config.LEGACY_XDG_CONFIG_FILE),
            )
            configpath = os.path.expanduser(Config.LEGACY_XDG_CONFIG_FILE)
        else:
            return

        if os.path.exists(os.path.expanduser(Config.LEGACY_XDG_CONFIG_FILE)):
            msg = (
                "The configuration mechanism of coBib underwent a major re-design for version 3.0! "
                "This means, that the old `INI`-style configuration is deprecated and will be "
                "fully removed on 1.1.2022. Instead, the configuration is now done through a "
                "Python file. For guidance on how to convert your existing configuration please "
                "consult the man-page or my blog post: "
                "https://mrossinek.gitlab.io/programming/cobibs-new-configuration/"
                "\nIf you have successfully migrated your configuration you should delete the old "
                "file in order to remove this warning message."
            )
            print("\x1b[1;37;41m#############\x1b[0m", file=sys.stderr)
            print("\x1b[1;37;41m## WARNING ##\x1b[0m", file=sys.stderr)
            print("\x1b[1;37;41m#############\x1b[0m", file=sys.stderr)
            print(msg, file=sys.stderr)

        spec = importlib.util.spec_from_file_location("config", configpath)
        if spec is None:
            LOGGER.warning(
                "The config at %s could not be interpreted as a Python module.", configpath
            )
            # attempt to load legacy INI configuration
            Config.load_legacy_config(configpath)
        else:
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)

        try:
            # validate config
            config.validate()
        except RuntimeError as exc:
            LOGGER.error(exc)
            sys.exit(1)

    @staticmethod
    def load_legacy_config(configpath):
        # pylint: disable=too-many-branches,too-many-nested-blocks
        """Loads a legacy `INI`-style configuration file.

        WARNING: This functionality will be removed on 1.1.2022! Users will be warned when using
        this configuration method.

        Args:
            configpath (str): the path to the configuration.
        """
        ini_conf = configparser.ConfigParser()
        ini_conf.optionxform = str  # makes option names case-sensitive!
        ini_conf.read(configpath)

        # We need to manually iterate all sections and fields because some settings need to be moved
        # and/or need to be converted to the correct Python types
        for section in ini_conf.sections():
            if section == "DATABASE":
                for field, value in dict(ini_conf[section]).items():
                    if field in ["file"]:
                        config.database[field] = value
                    elif field in ["git"]:
                        try:
                            config.database[field] = ini_conf[section].getboolean(field)
                        except ValueError as exc:
                            LOGGER.error(exc)
                            LOGGER.warning(
                                "Ignoring unknown option for %s/%s = %s", section, field, value
                            )
                    elif field == "open":
                        config.commands.open.command = value
                    elif field == "grep":
                        config.commands.search.grep = value
                    elif field == "search_ignore_case":
                        config.commands.search.ignore_case = ini_conf[section].getboolean(field)
                    else:
                        LOGGER.warning("Ignoring unknown setting %s", f"{section}/{field}")
            elif section == "FORMAT":
                for field, value in dict(ini_conf[section]).items():
                    if field == "default_entry_type":
                        config.commands.edit.default_entry_type = value
                    elif field == "ignore_non_standard_types":
                        try:
                            config.parsers.bibtex[field] = ini_conf[section].getboolean(field)
                        except ValueError as exc:
                            LOGGER.error(exc)
                            LOGGER.warning(
                                "Ignoring unknown option for %s/%s = %s", section, field, value
                            )
                    elif field == "month":
                        if value == "int":
                            config.database.format.month = int
                        elif value == "str":
                            config.database.format.month = str
                        else:
                            LOGGER.warning(
                                "Ignoring unknown option for %s/%s = %s", section, field, value
                            )
                    else:
                        LOGGER.warning("Ignoring unknown setting %s", f"{section}/{field}")
            elif section == "TUI":
                for field, value in dict(ini_conf[section]).items():
                    if field == "default_list_args":
                        config.tui[field] = value.split(" ")
                    elif field in ["prompt_before_quit", "reverse_order"]:
                        try:
                            config.tui[field] = ini_conf[section].getboolean(field)
                        except ValueError as exc:
                            LOGGER.error(exc)
                            LOGGER.warning(
                                "Ignoring unknown option for %s/%s = %s", section, field, value
                            )
                    elif field in ["scroll_offset"]:
                        try:
                            config.tui[field] = ini_conf[section].getint(field)
                        except ValueError as exc:
                            LOGGER.error(exc)
                            LOGGER.warning(
                                "Ignoring unknown option for %s/%s = %s", section, field, value
                            )
                    else:
                        LOGGER.warning("Ignoring unknown setting %s", f"{section}/{field}")
            elif section == "COLORS":
                for field, value in dict(ini_conf[section]).items():
                    config.tui.colors[field] = value
            elif section == "KEY_BINDINGS":
                for field, value in dict(ini_conf[section]).items():
                    config.tui.key_bindings[field.lower()] = value
            else:
                LOGGER.warning("Ignoring unknown config section %s", section)

    def validate(self):
        """Validates the configuration at runtime."""
        LOGGER.info("Validating the runtime configuration.")

        # LOGGING section
        LOGGER.debug("Validating the LOGGING configuration section.")
        self._assert(
            isinstance(self.logging.logfile, str), "config.logging.logfile should be a string."
        )

        # COMMANDS section
        LOGGER.debug("Validating the COMMANDS configuration section.")
        # COMMANDS.EDIT section
        LOGGER.debug("Validating the COMMANDS.EDIT configuration section.")
        self._assert(
            isinstance(self.commands.edit.default_entry_type, str),
            "config.commands.edit.default_entry_type should be a string.",
        )
        self._assert(
            isinstance(self.commands.edit.editor, str),
            "config.commands.edit.editor should be a string.",
        )
        # COMMANDS.OPEN section
        LOGGER.debug("Validating the COMMANDS.OPEN configuration section.")
        self._assert(
            isinstance(self.commands.open.command, str),
            "config.commands.open.command should be a string.",
        )
        # COMMANDS.SEARCH section
        LOGGER.debug("Validating the COMMANDS.SEARCH configuration section.")
        self._assert(
            isinstance(self.commands.search.grep, str),
            "config.commands.search.grep should be a string.",
        )
        self._assert(
            isinstance(self.commands.search.ignore_case, bool),
            "config.commands.search.ignore_case should be a boolean.",
        )

        # DATABASE section
        self._assert(
            isinstance(self.database.file, str), "config.database.file should be a string."
        )
        self._assert(
            isinstance(self.database.git, bool), "config.database.git should be a boolean."
        )
        # DATABASE.FORMAT section
        self._assert(
            self.database.format.month in (int, str),
            "config.database.format.month should be either the `int` or `str` type.",
        )
        self._assert(
            isinstance(self.database.format.suppress_latex_warnings, bool),
            "config.database.format.suppress_latex_warnings should be a boolean.",
        )

        # PARSER section
        self._assert(
            isinstance(self.parsers.bibtex.ignore_non_standard_types, bool),
            "config.parsers.bibtex.ignore_non_standard_types should be a boolean.",
        )

        # TUI section
        self._assert(
            isinstance(self.tui.default_list_args, list),
            "config.tui.default_list_args should be a list.",
        )
        self._assert(
            isinstance(self.tui.prompt_before_quit, bool),
            "config.tui.prompt_before_quit should be a boolean.",
        )
        self._assert(
            isinstance(self.tui.reverse_order, bool),
            "config.tui.reverse_order should be a boolean.",
        )
        self._assert(
            isinstance(self.tui.scroll_offset, int),
            "config.tui.scroll_offset should be an integer.",
        )

        # TUI.COLORS section
        LOGGER.debug("Validating the TUI.COLORS configuration section.")
        for name in self.DEFAULTS["tui"]["colors"].keys():
            self._assert(
                name in self.tui.colors.keys(), f"Missing config.tui.colors.{name} specification!"
            )

        for name, color in self.tui.colors.items():
            if name not in self.DEFAULTS["tui"]["colors"].keys() and name not in ANSI_COLORS:
                LOGGER.warning("Ignoring unknown TUI color: %s.", name)
            self._assert(
                color in ANSI_COLORS
                or (
                    len(color.strip("#")) == 6
                    and tuple(int(color.strip("#")[i : i + 2], 16) for i in (0, 2, 4))
                ),
                f"Unknown color specification: {color}",
            )

        # TUI.KEY_BINDINGS section
        LOGGER.debug("Validating the TUI.KEY_BINDINGS configuration section.")
        for command in self.DEFAULTS["tui"]["key_bindings"].keys():
            self._assert(
                command in self.tui.key_bindings.keys(),
                f"Missing config.tui.key_bindings.{command} key binding!",
            )
        for command, key in self.DEFAULTS["tui"]["key_bindings"].items():
            self._assert(
                isinstance(key, str), f"config.tui.key_bindings.{command} should be a string."
            )

    @staticmethod
    def _assert(expression, error):
        """Asserts the expression is True.

        Raises:
            RuntimeError with the specified error string.
        """
        if not expression:
            raise RuntimeError(error)

    def defaults(self):
        """Resets the configuration to the default settings."""
        for section in self.DEFAULTS.keys():
            self[section].update(**self.DEFAULTS[section])

    def get_ansi_color(self, name):
        """Returns an ANSI color code for the named color.

        Args:
            name (str): a named color as specified in the configuration *excluding* the `_fg` or
                        `_bg` suffix.

        Returns:
            A string representing the foreground and background ANSI color code.
        """
        fg_color = 30 + ANSI_COLORS.index(self.tui.colors.get(name + "_fg"))
        bg_color = 40 + ANSI_COLORS.index(self.tui.colors.get(name + "_bg"))

        return f"\x1b[{fg_color};{bg_color}m"


config = Config()
config.defaults()
