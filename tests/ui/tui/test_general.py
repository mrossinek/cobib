"""General tests for the TUI."""

from __future__ import annotations

from collections.abc import Generator
from copy import copy
from sys import version_info
from typing import Any

import pytest
from textual.theme import BUILTIN_THEMES

from cobib.config import config
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)


class TestTUIGeneral:
    """General tests for the TUI."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        config.load(get_resource("debug.py"))
        yield
        config.defaults()

    def test_main(self, snap_compare: Any) -> None:
        """Tests the main TUI.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE)

    def test_config_theme(self, snap_compare: Any) -> None:
        """Tests the config option to update the theme.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        a_splash_of_pink = copy(BUILTIN_THEMES["textual-dark"])
        a_splash_of_pink.primary = "#ff00ff"
        config.theme.theme = a_splash_of_pink
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("command_palette", [False, True])
    @pytest.mark.parametrize("answer", ["y", "n"])
    async def test_quit(self, command_palette: bool, answer: str) -> None:
        """Tests the quit action's input prompt.

        Args:
            command_palette: whether to trigger the quit action via the command palette.
            answer: the answer to the prompt. If `y`, the app should quit. If `n`, it should not.
        """
        app = TUI()

        async with app.run_test() as pilot:
            if command_palette:
                await pilot.press("ctrl+p")
                await pilot.press("q", "u", "i", "t")
                await pilot.press("enter")
            else:
                await pilot.press("q")

            await pilot.press(answer)
            await pilot.press("enter")
            await pilot.pause()

        if answer == "y":
            assert app.return_code == 0
        else:
            assert app.return_code is None

    @pytest.mark.skipif(
        version_info.minor < 12,
        reason="Textual datatable style updates appear inconsistent for Python < 3.12",
    )
    @pytest.mark.parametrize("repeat", [1, 2])
    def test_layout(self, snap_compare: Any, repeat: int) -> None:
        """Tests the layout toggle action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            repeat: the number of times to repeat the action trigger.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["underscore"] * repeat)

    @pytest.mark.parametrize("repeat", [1, 2])
    def test_help(self, snap_compare: Any, repeat: int) -> None:
        """Tests the help toggle action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            repeat: the number of times to repeat the action trigger.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["question_mark"] * repeat)

    @pytest.mark.parametrize("repeat", [1, 2])
    def test_select(self, snap_compare: Any, repeat: int) -> None:
        """Tests the select action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            repeat: the number of times to repeat the action trigger.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["v"] * repeat)

    def test_prompt(self, snap_compare: Any) -> None:
        """Tests the prompt popup.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["colon"])
