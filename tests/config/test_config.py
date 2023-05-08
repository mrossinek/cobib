"""Tests for coBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import logging
import os
from typing import Any, Generator, List

import pytest

from cobib.config import config
from cobib.config.config import Config

from .. import get_resource

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")


def test_config_init() -> None:
    """Test Config initialization."""
    # empty init
    assert Config() == {}  # pylint: disable=C1803
    # init from empty dictionary
    assert Config({}) == {}  # pylint: disable=C1803
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
    config.load()
    # we manually call validate because load exits early
    config.validate()


def test_config_disable_load() -> None:
    """Test that loading can be disabled via environment variable."""
    prev_value = os.environ.get("COBIB_CONFIG", None)
    try:
        config.database.file = "dummy"
        os.environ["COBIB_CONFIG"] = "0"
        config.load()
        assert config.database.file == "dummy"
    finally:
        if prev_value is None:
            os.environ.pop("COBIB_CONFIG", None)
        else:
            os.environ["COBIB_CONFIG"] = prev_value


def test_config_load_from_env_var() -> None:
    """Test that loading can be configured via environment variable."""
    prev_value = os.environ.get("COBIB_CONFIG", None)
    try:
        os.environ["COBIB_CONFIG"] = get_resource("debug.py")
        config.load()
        assert config.database.file == str(EXAMPLE_LITERATURE)
    finally:
        if prev_value is None:
            os.environ.pop("COBIB_CONFIG", None)
        else:
            os.environ["COBIB_CONFIG"] = prev_value


def test_config_load_xdg() -> None:
    """Test loading a config from XDG path."""
    Config.XDG_CONFIG_FILE = get_resource("debug.py")
    config.load()
    assert config.database.file == str(EXAMPLE_LITERATURE)


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
        [["commands", "list"], "ignore_case"],
        [["commands", "open"], "command"],
        [["commands", "open"], "fields"],
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
        [["parsers", "yaml"], "use_c_lib_yaml"],
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


@pytest.mark.parametrize(["setting", "value"], [])
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
