"""TUI tests affecting the list view."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from cobib.config import config
from cobib.database import Database
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)


class TestTUIList:
    """Tests for the `ListCommand` behavior inside the TUI."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        config.load(get_resource("debug.py"))
        yield
        Database.reset()
        config.defaults()

    def test_jump(self, snap_compare: Any) -> None:
        """Tests the jump action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(
            TUI(),
            terminal_size=TERMINAL_SIZE,
            press=[
                ":",
                "s",
                "h",
                "o",
                "w",
                "space",
                "e",
                "i",
                "n",
                "s",
                "t",
                "e",
                "i",
                "n",
                "enter",
            ],
        )

    def test_sort(self, snap_compare: Any) -> None:
        """Tests the sort action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(
            TUI(), terminal_size=TERMINAL_SIZE, press=["s", "y", "e", "a", "r", "enter"]
        )

    def test_filter(self, snap_compare: Any) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(
            TUI(),
            terminal_size=TERMINAL_SIZE,
            press=["f", "plus", "plus", "y", "e", "a", "r", "space", "1", "9", "0", "5", "enter"],
        )

    @pytest.mark.parametrize("prompt", [False, True])
    @pytest.mark.parametrize("reset", [False, True])
    def test_preset(self, snap_compare: Any, prompt: bool, reset: bool) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            prompt: whether to go via the prompt.
            reset: whether to reset the view by triggering the `0` preset.
        """
        config.tui.preset_filters = ["++year 1993"]
        press: list[str] = []
        if prompt:
            press.extend(["p", "down", "enter"])
        else:
            press.append("1")
        if reset:
            press.append("0")
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)

    @pytest.mark.parametrize(
        ("motions", "scroll_offset"),
        [
            (["down"], None),
            (["down", "up"], None),
            (["end"], None),
            (["end", "home"], None),
            (["pagedown"], None),
            (["end", "pageup"], None),
            (["pagedown"], 5),
            (["end", "pageup"], 5),
            (["right", "right"], None),
            (["right", "right", "left"], None),
        ],
    )
    def test_motion(self, snap_compare: Any, motions: list[str], scroll_offset: int | None) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            motions: the motions to perform.
            scroll_offset: the `config.tui.scroll_offset` value. `None` leaves the default value.
        """
        config.database.file = get_resource("scrolling.yaml", "ui/tui")
        if scroll_offset is not None:
            config.tui.scroll_offset = scroll_offset
        assert snap_compare(TUI(), terminal_size=(80, 24), press=motions)
