"""Tests for the dummy importer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest
from cobib_dummy.dummy_importer import DummyImporter

from cobib.config import config

from . import run_module


class TestDummyImporter:
    """Tests for the dummy importer."""

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
        """Test the command-line access of the importer.

        Args:
            setup: our custom configuration setup fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await run_module(monkeypatch, "main", ["cobib", "-p", "import", "--dummy"])

        out = capsys.readouterr().out.strip()
        assert "DummyImporter.fetch" in out
        assert "Imported 0 entries into the database." in out

    @pytest.mark.asyncio
    async def test_fetch(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the importer's fetch method.

        Args:
            capsys: the built-in pytest fixture.
        """
        importer = DummyImporter()
        fetched = await importer.fetch()
        assert fetched == []
        assert capsys.readouterr().out.strip() == "DummyImporter.fetch"
