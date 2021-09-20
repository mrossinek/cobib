"""Tests for coBib's logging helper functions."""

import logging
import re
import tempfile
from typing import Optional

import pytest

from cobib.utils.logging import get_file_handler, get_stream_handler, print_changelog

from .. import MockStdin, get_resource


def test_get_stream_handler() -> None:
    """Test stream logging configuration."""
    handler = get_stream_handler()
    assert handler.level == 30
    assert isinstance(handler, logging.StreamHandler)


def test_get_file_handler() -> None:
    """Test file logging configuration."""
    handler = get_file_handler("INFO")
    assert handler.level == 20
    assert isinstance(handler, logging.FileHandler)


@pytest.mark.parametrize("cached_version", [None, False, "", "0.1", "0.2"])
def test_print_changelog(
    cached_version: Optional[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test printing of the latest changelog section.

    Args:
        cached_version: the cached version to test against.
        monkeypatch: the built-in pytest fixture.
        capsys: the built-in pytest fixture.
    """
    monkeypatch.setattr("sys.stdin", MockStdin())
    ansi_regex = re.compile(r"(\x1b\[(\d+)+m)")
    if cached_version is None:
        print_changelog("0.2", None)
        assert capsys.readouterr().out == ""
    else:
        with tempfile.NamedTemporaryFile("w") as file:
            if not cached_version:
                file.close()
            else:
                file.write(cached_version)
                file.flush()
            print_changelog("0.2", file.name)
        captured = ansi_regex.sub("", capsys.readouterr().out).splitlines()
        if cached_version == "0.2":
            assert captured == []
        with open(
            get_resource("expected_changelog_printing.txt", "utils"), "r", encoding="utf-8"
        ) as expected:
            expected_lines = expected.read().splitlines()
            for true, exp in zip(captured[:-2], expected_lines):
                assert true == exp
            for true, exp in zip(captured[-2:], expected_lines[-2:]):
                assert true == exp
