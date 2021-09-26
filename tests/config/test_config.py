"""Tests for coBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import logging
import tempfile
from typing import Any, Generator, List

import pytest

from cobib.config import config
from cobib.config.config import Config

from .. import get_resource

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")


def test_config_init() -> None:
    """Test Config initialization."""
    # empty init
    assert Config() == {}
    # init from empty dictionary
    assert Config({}) == {}
    # init from dictionary
    assert Config({"dummy": "test"}) == {"dummy": "test"}
    # init from non-dictionary
    with pytest.raises(TypeError):
        Config(True)  # type: ignore
    with pytest.raises(TypeError):
        Config(1)  # type: ignore
    with pytest.raises(TypeError):
        Config("")  # type: ignore
    with pytest.raises(TypeError):
        Config([])  # type: ignore


def test_config_getattr() -> None:
    """Test the automatic attribute generation."""
    cfg = Config()
    dummy = cfg.dummy
    assert isinstance(cfg.dummy, Config)
    assert dummy == {}


def test_config_recursive_getattr() -> None:
    """Test the recursive attribute generation."""
    cfg = Config()
    dummy = cfg.dummy.dummy
    assert isinstance(cfg.dummy, Config)
    assert isinstance(cfg.dummy.dummy, Config)
    assert dummy == {}


def test_config_recursive_setattr() -> None:
    """Test the recursive attribute setting."""
    cfg = Config()
    cfg.dummy.dummy = "test"
    assert isinstance(cfg.dummy, Config)
    assert cfg.dummy.dummy == "test"
    assert cfg.dummy == {"dummy": "test"}


def test_config_load() -> None:
    """Test loading another config file."""
    config.load(get_resource("debug.py"))
    assert config.database.file == str(EXAMPLE_LITERATURE)


def test_config_load_from_open_file() -> None:
    """Test loading another config from an open file."""
    with open(get_resource("debug.py"), "r", encoding="utf-8") as file:
        config.load(file)
    assert config.database.file == str(EXAMPLE_LITERATURE)


def test_config_load_nothing() -> None:
    """Test that nothing changes when no XDG files are present."""
    Config.XDG_CONFIG_FILE = ""
    Config.LEGACY_XDG_CONFIG_FILE = ""
    config.load()
    # we manually call validate because load exits early
    config.validate()


def test_config_load_xdg() -> None:
    """Test loading a config from XDG path."""
    Config.XDG_CONFIG_FILE = get_resource("debug.py")
    config.load()
    assert config.database.file == str(EXAMPLE_LITERATURE)


# TODO: remove legacy configuration support on 1.1.2022
def assert_legacy_config() -> None:
    """Assert the legacy configuration has been applied."""
    assert config.commands.edit.default_entry_type == "string"
    assert config.commands.open.command == "string"
    assert config.commands.search.grep == "string"
    assert config.commands.search.ignore_case is True
    assert config.database.file == "string"
    assert config.database.git is True
    assert config.parsers.bibtex.ignore_non_standard_types is True
    assert config.tui.default_list_args == ["string"]
    assert config.tui.prompt_before_quit is False
    assert config.tui.reverse_order is False
    assert config.tui.scroll_offset == 5
    assert config.tui.colors.cursor_line_fg == "black"
    assert config.tui.key_bindings.prompt == "p"


def test_config_load_legacy() -> None:
    """Test loading a legacy config file."""
    config.load_legacy_config(get_resource("legacy_config.ini", "config"))
    # first, it must pass the validation test
    config.validate()
    # then we also check that all settings have been changed somehow
    assert_legacy_config()


def test_config_load_legacy_xdg() -> None:
    """Test loading a legacy config from XDG path."""
    Config.XDG_CONFIG_FILE = ""
    Config.LEGACY_XDG_CONFIG_FILE = get_resource("legacy_config.ini", "config")
    config.load()  # validation is done internally
    # then we also check that all settings have been changed somehow
    assert_legacy_config()


def test_config_example() -> None:
    """Test that the example config matches the default values."""
    config.clear()
    config.load(get_resource("example.py", "../src/cobib/config/"))
    assert config == Config.DEFAULTS


def test_config_validation_failure(caplog: pytest.LogCaptureFixture) -> None:
    """Test for a `SystemExit` upon config validation failure.

    Args:
        caplog: the built-in pytest fixture.
    """
    with pytest.raises(SystemExit):
        config.load(get_resource("broken_config.py", "config"))
    assert (
        "cobib.config.config",
        logging.ERROR,
        "config.database.file should be a string.",
    ) in caplog.record_tuples


@pytest.fixture
def setup() -> Generator[Any, None, None]:
    """Setup debugging configuration.

    Yields:
        Access to the local fixture variables.
    """
    config.load(get_resource("debug.py"))
    yield setup
    config.clear()
    config.defaults()


def test_config_validation(setup: Any) -> None:
    """Test that the initial configuration passes all validation checks.

    Args:
        setup: a local pytest fixture.
    """
    config.validate()


@pytest.mark.parametrize(
    ["sections", "field"],
    [
        [["logging"], "logfile"],
        [["logging"], "version"],
        [["commands", "edit"], "default_entry_type"],
        [["commands", "edit"], "editor"],
        [["commands", "open"], "command"],
        [["commands", "search"], "grep"],
        [["commands", "search"], "grep_args"],
        [["commands", "search"], "ignore_case"],
        [["database"], "file"],
        [["database"], "git"],
        [["database", "format"], "label_default"],
        [["database", "format"], "label_suffix"],
        [["database", "format"], "suppress_latex_warnings"],
        [["database", "stringify", "list_separator"], "file"],
        [["database", "stringify", "list_separator"], "tags"],
        [["database", "stringify", "list_separator"], "url"],
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
        [["utils", "file_downloader"], "default_location"],
        [["utils", "file_downloader"], "url_map"],
        [["utils"], "journal_abbreviations"],
    ],
)
def test_missing_config_fields(setup: Any, sections: List[str], field: str) -> None:
    """Test raised RuntimeError for missing config fields.

    Args:
        setup: a local pytest fixture.
        sections: a list of section names in the nested configuration.
        field: the name of the configuration setting.
    """
    with pytest.raises(RuntimeError) as exc_info:
        section = config
        for sec in sections[:-1]:
            section = section[sec]
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
def test_valid_tui_colors(setup: Any, color: str) -> None:
    """Test curses color specification validation.

    Args:
        setup: a local pytest fixture.
        color: the name of the color.
    """
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
def test_get_ansi_color(setup: Any, color: str, ansi: str) -> None:
    """Test default ANSI color code generation.

    Args:
        setup: a local pytest fixture.
        color: the name of the color.
        ansi: the expected ANSI code.
    """
    assert config.get_ansi_color(color) == ansi


def test_ignored_tui_color(setup: Any, caplog: pytest.LogCaptureFixture) -> None:
    """Test invalid TUI colors are ignored.

    Args:
        setup: a local pytest fixture.
        caplog: the built-in pytest fixture.
    """
    config.tui.colors.dummy = "white"
    config.validate()
    assert (
        "cobib.config.config",
        logging.WARNING,
        "Ignoring unknown TUI color: dummy.",
    ) in caplog.record_tuples


@pytest.mark.parametrize(["setting", "value"], [[["database", "format", "month"], str]])
def test_deprecation_warning(
    setting: List[str], value: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Test logged warning for deprecated setting.

    Args:
        setting: the list of attribute names leading to the deprecated setting.
        value: a value to use for the deprecated setting.
        caplog: the built-in pytest fixture.
    """
    section = config
    for sec in setting[:-1]:
        section = section[sec]
    section[setting[-1]] = value
    config.validate()
    for source, level, message in caplog.record_tuples:
        if (
            source == "cobib.config.config"
            and level == logging.WARNING
            and f"The config.{'.'.join(setting)} setting is deprecated" in message
        ):
            break
    else:
        assert False, "Missing deprecation warning!"


@pytest.mark.parametrize(
    ["setting", "attribute"], [["[FORMAT]\nmonth=str", "database.format.month"]]
)
def test_deprecation_warning_legacy(
    setting: str, attribute: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test logged warning for deprecated setting.

    Args:
        setting: the legacy formatted string of the deprecated setting.
        attribute: the new formatted name of the deprecated setting.
        caplog: the built-in pytest fixture.
    """
    with tempfile.NamedTemporaryFile("w") as legacy_file:
        legacy_file.write(setting)
        legacy_file.seek(0)
        config.load_legacy_config(legacy_file.name)
        config.validate()
    for source, level, message in caplog.record_tuples:
        if (
            source == "cobib.config.config"
            and level == logging.WARNING
            and f"The config.{attribute} setting is deprecated" in message
        ):
            break
    else:
        assert False, "Missing deprecation warning!"
