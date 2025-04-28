"""Tests for coBib's config validation."""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from typing import Any

import pytest

from cobib.config import config
from cobib.config.config import Config, LabelSuffix

from .. import get_resource

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")


def test_config_load() -> None:
    """Test loading another config file."""
    config.load(get_resource("debug.py"))
    assert config.database.file == str(EXAMPLE_LITERATURE)


def test_config_load_failure(caplog: pytest.LogCaptureFixture) -> None:
    """Test handling of an uninterpretable config.

    Args:
        caplog: the built-in pytest fixture.
    """
    path = get_resource("example_literature.yaml")
    with pytest.raises(SystemExit):
        config.load(path)
    assert (
        "cobib.config.config",
        logging.ERROR,
        f"The config at {path} could not be interpreted as a Python module.",
    ) in caplog.record_tuples


def test_config_load_from_open_file() -> None:
    """Test loading another config from an open file."""
    with open(get_resource("debug.py"), "r", encoding="utf-8") as file:
        config.load(file)
    assert config.database.file == str(EXAMPLE_LITERATURE)


def test_config_load_nothing() -> None:
    """Test that nothing changes when no XDG files are present."""
    prev = Config.XDG_CONFIG_FILE
    Config.XDG_CONFIG_FILE = ""
    try:
        config.load()
        # we manually call validate because load exits early
        config.validate()
    finally:
        Config.XDG_CONFIG_FILE = prev


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
    prev = Config.XDG_CONFIG_FILE
    Config.XDG_CONFIG_FILE = get_resource("debug.py")
    try:
        config.load()
        assert config.database.file == str(EXAMPLE_LITERATURE)
    finally:
        Config.XDG_CONFIG_FILE = prev


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


def test_label_suffix_type(setup: Any) -> None:
    """Test the `LabelSuffix.suffix_type` method.

    Args:
        setup: a local pytest fixture.
    """
    assert LabelSuffix.suffix_type("1") == LabelSuffix.NUMERIC
    assert LabelSuffix.suffix_type("10") == LabelSuffix.NUMERIC
    assert LabelSuffix.suffix_type("a") == LabelSuffix.ALPHA
    assert LabelSuffix.suffix_type("A") == LabelSuffix.CAPITAL
    assert LabelSuffix.suffix_type("-") is None
    assert LabelSuffix.suffix_type("_") is None
    assert LabelSuffix.suffix_type("Mixed") is None
    assert LabelSuffix.suffix_type("hello123") is None
    assert LabelSuffix.suffix_type("ä") is None


def test_label_suffix_reverse(setup: Any) -> None:
    """Test the `LabelSuffix.reverse` method.

    Args:
        setup: a local pytest fixture.
    """
    assert LabelSuffix.reverse(LabelSuffix.NUMERIC, "1") == 1
    assert LabelSuffix.reverse(LabelSuffix.NUMERIC, "12") == 12
    assert LabelSuffix.reverse(LabelSuffix.ALPHA, "a") == 1
    assert LabelSuffix.reverse(LabelSuffix.ALPHA, "z") == 26
    assert LabelSuffix.reverse(LabelSuffix.CAPITAL, "A") == 1
    assert LabelSuffix.reverse(LabelSuffix.CAPITAL, "Z") == 26

    with pytest.raises(ValueError):
        LabelSuffix.reverse(LabelSuffix.ALPHA, "ab")

    with pytest.raises(ValueError):
        LabelSuffix.reverse(LabelSuffix.ALPHA, "1")

    with pytest.raises(ValueError):
        LabelSuffix.reverse(LabelSuffix, "A")  # type: ignore[arg-type]


def test_label_suffix_trim(setup: Any) -> None:
    """Test the `LabelSuffix.trim` method.

    Args:
        setup: a local pytest fixture.
    """
    assert LabelSuffix.trim_label("Hello2024", "_", LabelSuffix.NUMERIC) == ("Hello2024", 0)
    assert LabelSuffix.trim_label("Hello2024", "_", LabelSuffix.ALPHA) == ("Hello2024", 0)
    assert LabelSuffix.trim_label("Hello2024", "_", LabelSuffix.CAPITAL) == ("Hello2024", 0)
    assert LabelSuffix.trim_label("Hello2024_1", "_", LabelSuffix.NUMERIC) == ("Hello2024", 1)
    assert LabelSuffix.trim_label("Hello2024_1", "_", LabelSuffix.ALPHA) == ("Hello2024_1", 0)
    assert LabelSuffix.trim_label("Hello2024_1", "_", LabelSuffix.CAPITAL) == ("Hello2024_1", 0)
    assert LabelSuffix.trim_label("Hello2024_2", "_", LabelSuffix.NUMERIC) == ("Hello2024", 2)
    assert LabelSuffix.trim_label("Hello2024_a", "_", LabelSuffix.NUMERIC) == ("Hello2024_a", 0)
    assert LabelSuffix.trim_label("Hello2024_a", "_", LabelSuffix.ALPHA) == ("Hello2024", 1)
    assert LabelSuffix.trim_label("Hello2024_b", "_", LabelSuffix.ALPHA) == ("Hello2024", 2)
    assert LabelSuffix.trim_label("Hello2024_A", "_", LabelSuffix.NUMERIC) == ("Hello2024_A", 0)
    assert LabelSuffix.trim_label("Hello2024_A", "_", LabelSuffix.CAPITAL) == ("Hello2024", 1)
    assert LabelSuffix.trim_label("Hello2024_B", "_", LabelSuffix.CAPITAL) == ("Hello2024", 2)
    assert LabelSuffix.trim_label("some_test", "_", LabelSuffix.NUMERIC) == ("some_test", 0)
    assert LabelSuffix.trim_label("some_test", "_", LabelSuffix.ALPHA) == ("some_test", 0)
    assert LabelSuffix.trim_label("some_test", "_", LabelSuffix.CAPITAL) == ("some_test", 0)
