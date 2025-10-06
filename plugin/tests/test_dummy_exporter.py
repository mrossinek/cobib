"""Tests for the dummy exporter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest
from cobib_dummy.dummy_exporter import DummyExporter

from cobib.config import config

from . import run_module


class TestDummyExporter:
    """Tests for the dummy exporter."""

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
        """Test the command-line access of the exporter.

        Args:
            setup: our custom configuration setup fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await run_module(monkeypatch, "main", ["cobib", "-p", "export", "--dummy"])

        out = capsys.readouterr().out.strip()
        assert "DummyExporter.write" in out

    def test_write(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the exporter's write method.

        Args:
            capsys: the built-in pytest fixture.
        """
        exporter = DummyExporter()
        exporter.write([])
        assert capsys.readouterr().out.strip() == "DummyExporter.write"
