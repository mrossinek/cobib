"""Tests for the dummy command."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator, cast

import pytest
from textual.pilot import Pilot

from cobib.config import config
from cobib.ui.tui import TUI

from . import run_module

TERMINAL_SIZE = (160, 48)


class TestDummyCommand:
    """Tests for the dummy command."""

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        """Loads the test configuration and restores the defaults after any test ran."""
        config.load(Path(__file__).parent / "debug.py")
        yield
        config.defaults()

    @pytest.mark.asyncio
    async def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await run_module(monkeypatch, "main", ["cobib", "-p", "dummy"])

        assert capsys.readouterr().out.strip() == "DummyCommand.execute"

    def test_handling_stdout(self, snap_compare: Any) -> None:
        """Tests the handling of output printed to `sys.stdout`.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("dummy", submit=True)
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_handling_stderr(self, snap_compare: Any) -> None:
        """Tests the handling of output printed to `sys.stderr`.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("dummy --stderr", submit=True)
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)
