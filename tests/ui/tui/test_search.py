"""TUI tests affecting the search view."""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any, cast

import pytest
from textual.pilot import Pilot

from cobib.config import config
from cobib.database import Database
from cobib.ui.components import InputScreen, LogScreen
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)


class TestTUISearch:
    """Tests for the `SearchCommand` behavior inside the TUI."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        InputScreen.cursor_blink = False
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

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("/19", submit=True)
            if expand:
                await pilot.press("space")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_empty_results(self, snap_compare: Any) -> None:
        """Test the handling of empty search results.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("/missing", submit=True)
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_expand_all(self, snap_compare: Any) -> None:
        """Tests the recursive expansion of all search result nodes.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        config.tui.tree_folding = (True, True)

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("/19", submit=True)
            await pilot.press("backspace")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_jump(self, snap_compare: Any) -> None:
        """Tests the jump action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("/19", submit=True)
            await app.action_prompt(":show latexcompanion")
            await pilot.press("enter")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_jump_missing(self, snap_compare: Any) -> None:
        """Tests the jump action handling for a missing entry.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
            app.logging_handler.setFormatter(formatter)
            log_screen = cast(LogScreen, app.get_screen("log"))
            log_screen.rich_log.clear()
            await app.action_prompt("/19", submit=True)
            await app.action_prompt(":show missing")
            await pilot.press("enter")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_jump_out_of_view(self, snap_compare: Any) -> None:
        """Tests the jump action handling for an existing entry that is out of view.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
            app.logging_handler.setFormatter(formatter)
            log_screen = cast(LogScreen, app.get_screen("log"))
            log_screen.rich_log.clear()
            await app.action_prompt("/19", submit=True)
            await app.action_prompt(":show knuthwebsite")
            await pilot.press("enter")
            await pilot.press("z")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    @pytest.mark.parametrize(
        "motions",
        [
            ["down"],
            ["down", "up"],
            ["end"],
            ["end", "home"],
            # TODO: figure out why the following tests are flaky
            pytest.param(
                ["pagedown"],
                marks=pytest.mark.skip(
                    reason="Not quite sure why, but this test is flaky since textual==5.0.0."
                ),
            ),
            pytest.param(
                ["end", "pageup"],
                marks=pytest.mark.skip(
                    reason="Not quite sure why, but this test is flaky since textual==5.0.0."
                ),
            ),
        ],
    )
    def test_motion(self, snap_compare: Any, motions: list[str]) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            motions: the motions to perform.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt("/19", submit=True)
            for button in motions:
                await pilot.press(button)
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)
