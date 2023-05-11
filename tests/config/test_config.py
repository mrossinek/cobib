"""Tests for coBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import logging
import os
from typing import Any, Generator

import pytest

from cobib.config import config
from cobib.config.config import Config

from .. import get_resource

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")


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
    config.load(get_resource("example.py", "../src/cobib/config/"))
    assert config == Config()


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
    config.defaults()


def test_config_validation(setup: Any) -> None:
    """Test that the initial configuration passes all validation checks.

    Args:
        setup: a local pytest fixture.
    """
    config.validate()
