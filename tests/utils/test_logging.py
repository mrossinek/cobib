"""Tests for coBib's logging helper functions."""

import logging
import re
import tempfile
from pathlib import Path
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
            path = Path(file.name)
            if not cached_version:
                file.close()
            else:
                file.write(cached_version)
                file.flush()
            print_changelog("0.2", str(path))
        # ensure we do not leave a temporary file behind
        if path.exists():
            path.unlink()
        captured = ansi_regex.sub("", capsys.readouterr().out).splitlines()
        if cached_version == "0.2":
            assert captured == []
        with open(
            get_resource("expected_changelog_printing.txt", "utils"), "r", encoding="utf-8"
        ) as expected:
            expected_lines = expected.read().splitlines()
            for true, exp in zip(captured[:-10], expected_lines):
                assert true == exp
            for true, exp in zip(captured[-2:], expected_lines[-2:]):
                assert true == exp


def test_safe_cache_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression test against #94.

    Args:
        monkeypatch: the built-in pytest fixture.
    """
    monkeypatch.setattr("sys.stdin", MockStdin())
    # create an empty temporary directory
    tmp_dir = tempfile.mkdtemp()
    # use a path which surely does not exist
    tmp_cache_file = Path(tmp_dir) / "cache/version"
    try:
        # try to read the version from a file whose parent directory does not exist
        print_changelog("0.2", str(tmp_cache_file))
        # if the test regresses, this will fail with a `FileNotFoundError`
    finally:
        if tmp_cache_file.exists():
            tmp_cache_file.unlink()
        if tmp_cache_file.parent.exists():
            tmp_cache_file.parent.rmdir()
        Path(tmp_dir).rmdir()
