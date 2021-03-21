"""Tests for coBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import logging

import pytest

from cobib.config import config
from cobib.config.config import Config

from .. import get_resource

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")


def test_config_init():
    """Test Config initialization."""
    # empty init
    assert Config() == {}
    # init from empty dictionary
    assert Config({}) == {}
    # init from dictionary
    assert Config({"dummy": "test"}) == {"dummy": "test"}
    # init from non-dictionary
    with pytest.raises(TypeError):
        Config(True)
    with pytest.raises(TypeError):
        Config(1)
    with pytest.raises(TypeError):
        Config("")
    with pytest.raises(TypeError):
        Config([])


def test_config_getattr():
    """Tests the automatic attribute generation."""
    cfg = Config()
    dummy = cfg.dummy
    assert isinstance(cfg.dummy, Config)
    assert dummy == {}


def test_config_recursive_getattr():
    """Tests the recursive attribute generation."""
    cfg = Config()
    dummy = cfg.dummy.dummy
    assert isinstance(cfg.dummy, Config)
    assert isinstance(cfg.dummy.dummy, Config)
    assert dummy == {}


def test_config_recursive_setattr():
    """Tests the recursive attribute setting."""
    cfg = Config()
    cfg.dummy.dummy = "test"
    assert isinstance(cfg.dummy, Config)
    assert cfg.dummy.dummy == "test"
    assert cfg.dummy == {"dummy": "test"}


def test_config_load():
    """Test loading another config file."""
    config.load(get_resource("debug.py"))
    assert config.database.file == EXAMPLE_LITERATURE


def test_config_load_from_open_file():
    """Test loading another config from an open file."""
    with open(get_resource("debug.py")) as file:
        config.load(file)
    assert config.database.file == EXAMPLE_LITERATURE


def test_config_load_nothing():
    """Test nothing changes when no XDG files are present."""
    Config.XDG_CONFIG_FILE = ""
    Config.LEGACY_XDG_CONFIG_FILE = ""
    config.load()
    # we manually call validate because load exits early
    config.validate()


def test_config_load_xdg():
    """Test loading config from XDG path."""
    Config.XDG_CONFIG_FILE = get_resource("debug.py")
    config.load()
    assert config.database.file == EXAMPLE_LITERATURE


# TODO: remove legacy configuration support on 1.1.2022
def assert_legacy_config():
    """Asserts the legacy configuration has been applied."""
    assert config.commands.edit.default_entry_type == "string"
    assert config.commands.open.command == "string"
    assert config.commands.search.grep == "string"
    assert config.commands.search.ignore_case is True
    assert config.database.file == "string"
    assert config.database.git is True
    assert config.database.format.month == str
    assert config.parsers.bibtex.ignore_non_standard_types is True
    assert config.tui.default_list_args == ["string"]
    assert config.tui.prompt_before_quit is False
    assert config.tui.reverse_order is False
    assert config.tui.scroll_offset == 5
    assert config.tui.colors.cursor_line_fg == "black"
    assert config.tui.key_bindings.prompt == "p"


def test_config_load_legacy():
    """Test loading a legacy config file."""
    config.load_legacy_config(get_resource("legacy_config.ini", "config"))
    # first, it must pass the validation test
    config.validate()
    # then we also check that all settings have been changed somehow
    assert_legacy_config()


def test_config_load_legacy_xdg():
    """Test loading a legacy config from XDG path."""
    Config.XDG_CONFIG_FILE = ""
    Config.LEGACY_XDG_CONFIG_FILE = get_resource("legacy_config.ini", "config")
    config.load()  # validation is done internally
    # then we also check that all settings have been changed somehow
    assert_legacy_config()


def test_config_example():
    """Test the example config."""
    config.clear()
    config.load(get_resource("example.py", "../src/cobib/config/"))
    assert config == Config.DEFAULTS


def test_config_validation_failure(caplog):
    """Tests SystemExit upon config validation failure."""
    with pytest.raises(SystemExit):
        config.load(get_resource("broken_config.py", "config"))
    assert (
        "cobib.config.config",
        logging.ERROR,
        "config.database.file should be a string.",
    ) in caplog.record_tuples


@pytest.fixture
def setup():
    """Setup debugging configuration."""
    config.load(get_resource("debug.py"))
    yield setup
    config.clear()
    config.defaults()


def test_config_validation(setup):
    """Test the initial configuration passes all validation checks."""
    config.validate()


@pytest.mark.parametrize(
    ["sections", "field"],
    [
        [["logging"], "logfile"],
        [["commands", "edit"], "default_entry_type"],
        [["commands", "edit"], "editor"],
        [["commands", "open"], "command"],
        [["commands", "search"], "grep"],
        [["commands", "search"], "ignore_case"],
        [["database"], "file"],
        [["database"], "git"],
        [["database", "format"], "month"],
        [["database", "format"], "suppress_latex_warnings"],
        [["parsers", "bibtex"], "ignore_non_standard_types"],
        [["tui"], "default_list_args"],
        [["tui"], "prompt_before_quit"],
        [["tui"], "reverse_order"],
        [["tui"], "scroll_offset"],
        [["tui", "colors"], "cursor_line_fg"],
        [["tui", "colors"], "cursor_line_bg"],
        [["tui", "colors"], "top_statusbar_fg"],
        [["tui", "colors"], "top_statusbar_bg"],
        [["tui", "colors"], "bottom_statusbar_fg"],
        [["tui", "colors"], "bottom_statusbar_bg"],
        [["tui", "colors"], "search_label_fg"],
        [["tui", "colors"], "search_label_bg"],
        [["tui", "colors"], "search_query_fg"],
        [["tui", "colors"], "search_query_bg"],
        [["tui", "colors"], "popup_help_fg"],
        [["tui", "colors"], "popup_help_bg"],
        [["tui", "colors"], "popup_stdout_fg"],
        [["tui", "colors"], "popup_stdout_bg"],
        [["tui", "colors"], "popup_stderr_fg"],
        [["tui", "colors"], "popup_stderr_bg"],
        [["tui", "colors"], "selection_fg"],
        [["tui", "colors"], "selection_bg"],
        [["tui", "key_bindings"], "prompt"],
        [["tui", "key_bindings"], "search"],
        [["tui", "key_bindings"], "help"],
        [["tui", "key_bindings"], "add"],
        [["tui", "key_bindings"], "delete"],
        [["tui", "key_bindings"], "edit"],
        [["tui", "key_bindings"], "filter"],
        [["tui", "key_bindings"], "modify"],
        [["tui", "key_bindings"], "open"],
        [["tui", "key_bindings"], "quit"],
        [["tui", "key_bindings"], "redo"],
        [["tui", "key_bindings"], "sort"],
        [["tui", "key_bindings"], "undo"],
        [["tui", "key_bindings"], "select"],
        [["tui", "key_bindings"], "wrap"],
        [["tui", "key_bindings"], "export"],
        [["tui", "key_bindings"], "show"],
    ],
)
def test_missing_config_fields(setup, sections, field):
    """Test raised RuntimeError for missing config fields."""
    with pytest.raises(RuntimeError) as exc_info:
        section = config
        for sec in sections[:-1]:
            section = config[sec]
        del section[sections[-1]][field]
        config.validate()
    assert f"config.{'.'.join(sections)}.{field}" in str(exc_info.value)


@pytest.mark.parametrize(
    ["color"],
    [
        ["cursor_line_fg"],
        ["cursor_line_bg"],
        ["top_statusbar_fg"],
        ["top_statusbar_bg"],
        ["bottom_statusbar_fg"],
        ["bottom_statusbar_bg"],
        ["search_label_fg"],
        ["search_label_bg"],
        ["search_query_fg"],
        ["search_query_bg"],
        ["popup_help_fg"],
        ["popup_help_bg"],
        ["popup_stdout_fg"],
        ["popup_stdout_bg"],
        ["popup_stderr_fg"],
        ["popup_stderr_bg"],
        ["selection_fg"],
        ["selection_bg"],
    ],
)
def test_valid_tui_colors(setup, color):
    """Test curses color specification validation."""
    with pytest.raises(RuntimeError) as exc_info:
        config.tui.colors[color] = "test"
        config.validate()
    assert str(exc_info.value) == "Unknown color specification: test"


@pytest.mark.parametrize(
    ["color", "ansi"],
    [
        ["cursor_line", "\x1b[37;46m"],
        ["top_statusbar", "\x1b[30;43m"],
        ["bottom_statusbar", "\x1b[30;43m"],
        ["search_label", "\x1b[34;40m"],
        ["search_query", "\x1b[31;40m"],
        ["popup_help", "\x1b[37;42m"],
        ["popup_stdout", "\x1b[37;44m"],
        ["popup_stderr", "\x1b[37;41m"],
        ["selection", "\x1b[37;45m"],
    ],
)
def test_get_ansi_color(setup, color, ansi):
    """Test default ANSI color code generation."""
    assert config.get_ansi_color(color) == ansi


def test_ignored_tui_color(setup, caplog):
    """Test invalid TUI colors are ignored."""
    config.tui.colors.dummy = "white"
    config.validate()
    assert (
        "cobib.config.config",
        logging.WARNING,
        "Ignoring unknown TUI color: dummy.",
    ) in caplog.record_tuples
