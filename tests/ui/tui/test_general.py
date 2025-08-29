"""General tests for the TUI."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Generator
from copy import copy
from pathlib import Path
from shutil import copyfile, rmtree
from sys import version_info
from typing import Any, cast

import pytest
from textual.pilot import Pilot
from textual.theme import BUILTIN_THEMES

from cobib.config import TagMarkup, config
from cobib.database import Database
from cobib.ui.components import InputScreen, LogScreen
from cobib.ui.tui import TUI

from ... import get_resource

TERMINAL_SIZE = (160, 48)
TMPDIR = Path(tempfile.gettempdir()).resolve()


class TestTUIGeneral:
    """General tests for the TUI."""

    COBIB_TEST_DIR = TMPDIR / "cobib_test"
    """Path to the temporary coBib test directory."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        InputScreen.cursor_blink = False
        config.load(get_resource("debug.py"))
        yield
        Database.read()
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

    def test_config_syntax(self, snap_compare: Any) -> None:
        """Tests the config option to update the syntax theme.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        config.theme.syntax.theme = "vim"
        config.theme.syntax.background_color = "#222222"
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE)

    def test_config_user_tags(self, snap_compare: Any) -> None:
        """Tests the config option to update the theme.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
        config.theme.tags.user_tags = {"test": TagMarkup(50, "black on yellow")}
        config.theme.tags.validate()
        bib = Database()
        bib["einstein"].tags = ["test"]
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

    @pytest.mark.asyncio
    async def test_quit_after_cancel(self) -> None:
        """Tests the quit action's input prompt after previously cancelling it."""
        app = TUI()

        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.press("escape")
            await pilot.press("n")
            await pilot.press("enter")
            await pilot.press("q")
            await pilot.press("y")
            await pilot.press("enter")
            await pilot.pause()

        assert app.return_code == 0

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

    @pytest.mark.parametrize("close", [False, True])
    def test_log(self, snap_compare: Any, close: bool) -> None:
        """Tests the log toggle action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            close: whether to close the LogScreen again.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
            app.logging_handler.setFormatter(formatter)
            log_screen = cast(LogScreen, app.get_screen("log"))
            log_screen.rich_log.clear()
            logger = logging.getLogger("cobib.ui.tui")
            logger.log(logging.DEBUG, "debug message")
            logger.log(logging.INFO, "info message")
            logger.log(35, "hint message")
            logger.log(logging.WARNING, "warning message")
            logger.log(45, "deprecation message")
            logger.log(logging.ERROR, "error message")
            logger.log(logging.CRITICAL, "critical message")
            if close:
                await pilot.press("z")
            await pilot.pause()

        assert snap_compare(
            TUI(verbosity=logging.DEBUG), terminal_size=TERMINAL_SIZE, run_before=run_before
        )

    @pytest.mark.parametrize("repeat", [1, 2])
    def test_help(self, snap_compare: Any, repeat: int) -> None:
        """Tests the help toggle action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            repeat: the number of times to repeat the action trigger.
        """
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["question_mark"] * repeat)

    @pytest.mark.skipif(
        version_info.minor < 13,
        reason="Formatting of the --help notification popups varies between Python versions.",
    )
    @pytest.mark.parametrize("command", ["delete", "init", "git", "list", "man", "show", "search"])
    def test_help_notification(self, snap_compare: Any, command: str) -> None:
        """Tests the notification system for command `--help`.

        This is a regression test against: https://gitlab.com/cobib/cobib/-/issues/161
        We test the `--help` output for a non-specially treated command and all those commands that
        are treated specially during `TUI.action_prompt`.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            command: the command whose `--help` to request.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt(f":{command} --help", submit=True)
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    @pytest.mark.parametrize(
        "extra_keys",
        [
            [],
            ["t"],  # ToC
            ["q"],  # quit
            ["q", "!"],  # continue where we left (do not open man-page index)
            ["j"] * 5 + ["k"],
        ],
    )
    def test_manpage(self, snap_compare: Any, extra_keys: list[str]) -> None:
        """Tests loading a specific man-page.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            extra_keys: any extra keys to press.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            await app.action_prompt(":man cobib.1", submit=True)
            for key in extra_keys:
                await pilot.press(key)
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    @pytest.mark.parametrize(
        "extra_keys",
        [
            [],
            ["escape"],  # dismiss
            ["enter"],  # select
            # NOTE: in the test below we scroll far enough to cause a visual update to the
            # OptionList but not too far such that the output is independent of whether or not
            # plugin man-pages are registered.
            ["j"] * 19 + ["k"],  # scroll up and down
        ],
    )
    def test_manpage_index(self, snap_compare: Any, extra_keys: list[str]) -> None:
        """Tests the man-page index screen.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            extra_keys: any extra keys to press.
        """
        press = ["exclamation_mark", *extra_keys]
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)

    @pytest.mark.parametrize("press", [["enter"], ["j"], ["d"], ["e"], ["o"], ["v"]])
    def test_empty_database(self, snap_compare: Any, press: list[str]) -> None:
        """Tests the handling of an empty database.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            press: what keys to press.
        """
        old_database_file = config.database.file
        new_database_file = self.COBIB_TEST_DIR / "database.yaml"
        self.COBIB_TEST_DIR.mkdir(parents=True, exist_ok=True)
        new_database_file.touch()
        config.database.file = new_database_file
        Database.read()

        try:
            assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)
        finally:
            config.database.file = old_database_file
            Database.read()
            rmtree(self.COBIB_TEST_DIR)

    @pytest.mark.parametrize("escape", [False, True])
    def test_prompt_action(self, snap_compare: Any, escape: bool) -> None:
        """Tests the coBib command prompt popup.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            escape: whether to also press the `escape` key.
        """
        press = ["colon"]
        if escape:
            press += ["escape"]
        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=press)

    def test_prompt_ask(self, snap_compare: Any) -> None:
        """Tests the prompt input screen when asked an interactive question using the `open` action.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """
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

        try:
            assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, press=["o"])
        finally:
            config.database.file = old_database_file
            Database.read()
            rmtree(self.COBIB_TEST_DIR)

    def test_prompt_elaborate(self, snap_compare: Any) -> None:
        """Tests the prompt in a more elaborate way via the `review` command.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            await pilot.press("c", "enter")  # starts a review process
            await pilot.press("h", "e", "l", "p", "enter")  # triggers the help popup
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)

    @pytest.mark.parametrize("command", ["init", "git", "faulty"])
    def test_catch_invalid_command(self, snap_compare: Any, command: str) -> None:
        """Tests the graceful catching of commands that cannot run within the TUI.

        Args:
            snap_compare: the `pytest-textual-snapshot` fixture.
            command: the command to trigger via the TUI's prompt action.
        """

        async def run_before(pilot: Pilot[None]) -> None:
            app = cast(TUI, pilot.app)
            formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
            app.logging_handler.setFormatter(formatter)
            log_screen = cast(LogScreen, app.get_screen("log"))
            log_screen.rich_log.clear()
            await app.action_prompt(command)
            await pilot.press("enter")
            await pilot.pause()

        assert snap_compare(TUI(), terminal_size=TERMINAL_SIZE, run_before=run_before)
