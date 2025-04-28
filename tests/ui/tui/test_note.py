"""TUI tests affecting the note view."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile, rmtree
from typing import Any

import pytest
from textual.pilot import Pilot

from cobib.config import config
from cobib.database import Database
from cobib.ui.components import InputScreen
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)
TMPDIR = Path(tempfile.gettempdir()).resolve()


class TestTUINote:
    """TUI tests affecting the note view."""

    COBIB_TEST_DIR = TMPDIR / "cobib_test"
    """Path to the temporary coBib test directory."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        InputScreen.cursor_blink = False
        config.load(get_resource("debug.py"))
        old_database_file = config.database.file
        new_database_file = str(TestTUINote.COBIB_TEST_DIR / "database.yaml")
        config.database.file = new_database_file
        TestTUINote.COBIB_TEST_DIR.mkdir(parents=True, exist_ok=True)
        copyfile(get_resource("example_literature.yaml", None), config.database.file)
        Database.read()
        yield
        config.database.file = old_database_file
        Path(new_database_file).unlink(missing_ok=True)
        rmtree(TestTUINote.COBIB_TEST_DIR)
        Database.read()
        config.defaults()

    def test_note_edit(self, snap_compare: Any) -> None:
        """Tests the editing of a new note.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            await pilot.press("n")
            await pilot.press("t", "e", "s", "t")
            await pilot.press("ctrl+s")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

        expected_note_path = self.COBIB_TEST_DIR / "knuthwebsite.txt"
        assert expected_note_path.exists()

        assert open(expected_note_path).read() == "test"

    def test_note_reset(self, snap_compare: Any) -> None:
        """Tests resetting the editing a note.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            await pilot.press("n")
            await pilot.press("t", "e", "s", "t")
            await pilot.press("ctrl+r")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

        expected_note_path = self.COBIB_TEST_DIR / "knuthwebsite.txt"
        assert not expected_note_path.exists()

    def test_note_unsaved_quit(self, snap_compare: Any) -> None:
        """Tests quitting does not work with an unsaved note.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            await pilot.press("n")
            await pilot.press("t", "e", "s", "t")
            await pilot.press("escape")
            await pilot.press("q")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

        expected_note_path = self.COBIB_TEST_DIR / "knuthwebsite.txt"
        assert not expected_note_path.exists()

    def test_note_unsaved_open_another(self, snap_compare: Any) -> None:
        """Tests opening another note does not work with another is unsaved.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            await pilot.press("n")
            await pilot.press("t", "e", "s", "t")
            await pilot.press("escape")
            await pilot.press("j")
            await pilot.press("n")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

        expected_note_path = self.COBIB_TEST_DIR / "knuthwebsite.txt"
        assert not expected_note_path.exists()
