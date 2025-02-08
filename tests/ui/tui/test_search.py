"""TUI tests affecting the search view."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from cobib.config import config
from cobib.database import Database
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)


class TestTUISearch:
    """Tests for the `SearchCommand` behavior inside the TUI."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        config.load(get_resource("debug.py"))
        yield
        Database.reset()
        config.defaults()

    @pytest.mark.parametrize("expand", [False, True])
    @pytest.mark.parametrize(
        "tree_folding", [None, (False, False), (False, True), (True, False), (True, True)]
    )
    def test_search(
        self, snap_compare: Any, expand: bool, tree_folding: tuple[bool, bool] | None
    ) -> None:
        """Tests the basic search result view.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            expand: whether to expand the tree node.
            tree_folding: the `config.tui.tree_folding` value. `None` leaves the default value.
        """
        if tree_folding is not None:
            config.tui.tree_folding = tree_folding
        press = ["slash", "1", "9", "enter"]
        if expand:
            press.append("space")
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)

    def test_expand_all(self, snap_compare: Any) -> None:
        """Tests the recursive expansion of all search result nodes.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        config.tui.tree_folding = (True, True)
        press = ["slash", "1", "9", "enter", "backspace"]
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)

    def test_jump(self, snap_compare: Any) -> None:
        """Tests the jump action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(
            TUI(),
            terminal_size=TERMINAL_SIZE,
            press=[
                "slash",
                "1",
                "9",
                "enter",
                ":",
                "s",
                "h",
                "o",
                "w",
                "space",
                "l",
                "a",
                "t",
                "e",
                "x",
                "c",
                "o",
                "m",
                "p",
                "a",
                "n",
                "i",
                "o",
                "n",
                "enter",
            ],
        )

    @pytest.mark.parametrize(
        "motions",
        [
            ["down"],
            ["down", "up"],
            ["end"],
            ["end", "home"],
            ["pagedown"],
            ["end", "pageup"],
        ],
    )
    def test_motion(self, snap_compare: Any, motions: list[str]) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            motions: the motions to perform.
        """
        press = ["slash", "1", "9", "enter", *motions]
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)
