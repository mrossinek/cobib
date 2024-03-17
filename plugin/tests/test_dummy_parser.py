"""Tests for the dummy parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest
from cobib_dummy.dummy_parser import DummyParser

from cobib.config import config
from cobib.database import Entry

from . import run_module


class TestDummyParser:
    """Tests for the dummy parser."""

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        """Loads the test configuration and restores the defaults after any test ran."""
        config.load(Path(__file__).parent / "debug.py")
        yield
        config.defaults()

    @pytest.mark.asyncio
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the parser.

        Args:
            setup: our custom configuration setup fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await run_module(monkeypatch, "main", ["cobib", "-p", "add", "--dummy", ""])

        assert capsys.readouterr().out.strip() == "DummyParser.parse"

    def test_dump(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the parser's dump method.

        Args:
            capsys: the built-in pytest fixture.
        """
        parser = DummyParser()
        entry = Entry("label", {})
        dumped = parser.dump(entry)
        assert dumped is None
        assert capsys.readouterr().out.strip() == "DummyParser.dump"

    def test_parse(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the parser's parse method.

        Args:
            capsys: the built-in pytest fixture.
        """
        parser = DummyParser()
        entry = parser.parse("")
        assert entry == {}
        assert capsys.readouterr().out.strip() == "DummyParser.parse"
