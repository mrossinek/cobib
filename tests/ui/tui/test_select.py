"""Selection tests for the TUI."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile
from sys import version_info
from typing import Any, cast

import pytest
from textual.pilot import Pilot

from cobib.config import config
from cobib.database import Database
from cobib.ui.components import InputScreen
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)
TMPDIR = Path(tempfile.gettempdir()).resolve()


class TestTUISelection:
    """Selection tests for the TUI."""

    COBIB_TEST_DIR = TMPDIR / "cobib_test"
    """Path to the temporary coBib test directory."""

    # Note: we can hard-code the `/tmp` path here, because we never really create these files.
    # We just need some absolute paths to test against.
    TMP_FILE_A = "/tmp/a.txt"
    TMP_FILE_B = "/tmp/b.txt"

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        InputScreen.cursor_blink = False
        config.load(get_resource("debug.py"))
        yield
        Database.read()
        config.defaults()

    @pytest.fixture
    def post_setup(self) -> Generator[Any, None, None]:
        """Additional setup instructions."""
        old_database_file = config.database.file
        new_database_file = str(self.COBIB_TEST_DIR / "database.yaml")
        config.database.file = new_database_file
        self.COBIB_TEST_DIR.mkdir(parents=True, exist_ok=True)
        copyfile(get_resource("example_literature.yaml", None), config.database.file)

        with open(
            get_resource("example_multi_file_entry.yaml", "commands"), "r", encoding="utf-8"
        ) as multi_file_entry:
            with open(config.database.file, "a", encoding="utf-8") as database:
                database.write(multi_file_entry.read())
        Database.read()

        yield

        config.database.file = old_database_file
        Database.read()
        Path(new_database_file).unlink(missing_ok=True)

    @pytest.mark.parametrize("repeat", [1, 2])
    def test_select(self, snap_compare: Any, repeat: int) -> None:
        """Tests the basic select action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            repeat: the number of times to repeat the action trigger.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["v"] * repeat)

    def test_delete(self, post_setup: Any, snap_compare: Any) -> None:
        """Tests the delete command with an active selection.

        Args:
            post_setup: an additional setup fixture.
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            await pilot.press("end")  # jumps to the final entry (`einstein`)
            await pilot.press("v")  # selects the current entry
            await pilot.press("k")  # move out of the way
            await pilot.press("d", "y", "enter")  # delete the selected (!) entry
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

        assert "einstein" not in Database()

    def test_open(self, post_setup: Any, snap_compare: Any) -> None:
        """Tests the open command with an active selection.

        Args:
            post_setup: an additional setup fixture.
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["v", "j", "o"])

    @pytest.mark.skipif(
        version_info.minor < 12,
        reason="Not quite sure why, but the output differs consistently in these cases.",
    )
    def test_prompt_with_selection(self, post_setup: Any, snap_compare: Any) -> None:
        """Tests the handling of an active selection during an interactive command prompt.

        This leverages the `modify` command to test the behavior works as intended.

        Args:
            post_setup: an additional setup fixture.
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await pilot.press("end")  # jumps to the final entry (`einstein`)
            await pilot.press("v")  # selects the current entry
            await app.action_prompt("modify 'year:2025'", submit=True)
            await pilot.press("enter")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

        assert Database()["einstein"].data["year"] == 2025
