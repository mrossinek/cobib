"""TUI tests affecting the list view."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile, rmtree
from typing import Any, cast

import pytest
from textual.pilot import Pilot

from cobib.config import config
from cobib.database import Database
from cobib.ui.components import InputScreen, LogScreen
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)
TMPDIR = Path(tempfile.gettempdir()).resolve()


class TestTUIList:
    """Tests for the `ListCommand` behavior inside the TUI."""

    COBIB_TEST_DIR = TMPDIR / "cobib_test"
    """Path to the temporary coBib test directory."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        InputScreen.cursor_blink = False
        config.load(get_resource("debug.py"))
        yield
        Database.reset()
        config.defaults()

    def test_jump(self, snap_compare: Any) -> None:
        """Tests the jump action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt(":show einstein")
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
            await app.action_filter()
            await pilot.press("minus", "minus", "y", "e", "a", "r", "space", "1", "9", "enter")
            await app.action_prompt(":show einstein")
            await pilot.press("enter")
            await pilot.press("z")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_sort(self, snap_compare: Any) -> None:
        """Tests the sort action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_sort()
            await pilot.press("y", "e", "a", "r", "enter")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    @pytest.mark.parametrize("first_sort", ["enter", "escape"])
    def test_sort_twice(self, snap_compare: Any, first_sort: str) -> None:
        """Tests the prompt when sort is called for the second time.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            first_sort: how to finish the first sort command: accept or abort it.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_sort()
            await pilot.press("y", "e", "a", "r", first_sort)
            await app.action_sort()
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    def test_filter(self, snap_compare: Any) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_filter()
            await pilot.press(
                "plus", "plus", "y", "e", "a", "r", "space", "1", "9", "0", "5", "enter"
            )
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    @pytest.mark.parametrize(
        "press",
        [
            ["1"],  # go to the first filter
            ["1", "0"],  # go back to main screen
            ["p"],  # open the prompt
            ["p", "q"],  # cancel the prompt
            ["p", "enter"],  # select the NONE preset
            ["p", "down", "enter"],  # select the first preset
        ],
    )
    def test_preset(self, snap_compare: Any, press: list[str]) -> None:
        """Tests the filter action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            press: the sequence of keys to press.
        """
        config.tui.preset_filters = ["++year 1993"]
        config.tui.validate()
        try:
            assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)
        finally:
            config.tui.preset_filters = []

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

    @pytest.mark.parametrize("answer", [None, "n", "y"])
    def test_delete(self, snap_compare: Any, answer: str | None) -> None:
        """Tests the delete action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            answer: the answer to the confirmation prompt.
        """
        self.COBIB_TEST_DIR.mkdir(parents=True, exist_ok=True)
        config.database.file = str(self.COBIB_TEST_DIR / "database.yaml")
        copyfile(get_resource("example_literature.yaml"), config.database.file)

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            app.action_delete()
            if answer is not None:
                await pilot.press(answer, "enter")
            await pilot.pause()

        try:
            assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)
        finally:
            rmtree(self.COBIB_TEST_DIR)
