"""Tests for coBib's RedoCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import contextlib
import logging
import os
import subprocess
from argparse import Namespace
from io import StringIO
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any, Type

import pytest

from cobib.commands import AddCommand, RedoCommand, UndoCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

EXAMPLE_MULTI_FILE_ENTRY_BIB = get_resource("example_multi_file_entry.bib", "commands")

if TYPE_CHECKING:
    import cobib.commands


class TestRedoCommand(CommandTest, TUITest):
    """Tests for coBib's RedoCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return RedoCommand

    def _assert(self) -> None:
        """Common assertion utility method."""
        assert Database().get("example_multi_file_entry", None) is not None

        # get last commit message
        with subprocess.Popen(
            ["git", "-C", self.COBIB_TEST_DIR, "show", "--format=format:%B", "--no-patch", "HEAD"],
            stdout=subprocess.PIPE,
        ) as proc:
            message, _ = proc.communicate()
            # decode it
            split_message = message.decode("utf-8").split("\n")
            # assert subject line
            assert "Redo" in split_message[0]

    @pytest.mark.parametrize(
        ["setup", "expected_exit"],
        [
            [{"git": False}, False],
            [{"git": True}, False],
            [{"git": True}, True],
        ],
        indirect=["setup"],
    )
    def test_command(
        self, setup: Any, expected_exit: bool, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            expected_exit: whether to expect an early exit.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        if not git:
            RedoCommand().execute([])
            for (source, level, message) in caplog.record_tuples:
                if ("cobib.commands.redo", logging.ERROR) == (
                    source,
                    level,
                ) and "git-tracking" in message:
                    break
            else:
                pytest.fail("No Error logged from RedoCommand.")
        elif expected_exit:
            # Regression test against #65
            AddCommand().execute(["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
            with pytest.raises(SystemExit):
                RedoCommand().execute([])
            for (source, level, message) in caplog.record_tuples:
                if ("cobib.commands.redo", logging.WARNING) == (
                    source,
                    level,
                ) and "Could not find a commit to redo." in message:
                    break
            else:
                pytest.fail("No Error logged from UndoCommand.")
        else:
            AddCommand().execute(["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
            UndoCommand().execute([])

            if Database().get("example_multi_file_entry", None) is not None:
                pytest.skip("UndoCommand failed. No point in attempting Redo.")

            RedoCommand().execute([])

            self._assert()

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_skipping_redone_commits(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test skipping already redone commits.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        AddCommand().execute(["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
        AddCommand().execute(["-b", get_resource("example_entry.bib")])
        UndoCommand().execute([])
        UndoCommand().execute([])
        RedoCommand().execute([])
        caplog.clear()

        RedoCommand().execute([])
        self._assert()
        assert "Storing redone commit" in caplog.record_tuples[4][2]
        assert "Skipping" in caplog.record_tuples[6][2]

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_warn_insufficient_setup(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning in case of insufficient setup.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        rmtree(self.COBIB_TEST_DIR_GIT)
        RedoCommand().execute([])
        for (source, level, message) in caplog.record_tuples:
            if ("cobib.commands.redo", logging.ERROR) == (
                source,
                level,
            ) and "configured, but not initialized" in message:
                break
        else:
            pytest.fail("No Error logged from RedoCommand.")

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    # other variants are already covered by test_command
    def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
        """
        AddCommand().execute(["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
        UndoCommand().execute([])

        if Database().get("example_multi_file_entry", None) is not None:
            pytest.skip("UndoCommand failed. No point in attempting Redo.")

        self.run_module(monkeypatch, "main", ["cobib", "redo"])

        self._assert()

    # manually overwrite this test because we must enable git integration
    def test_handle_argument_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of ArgumentError.

        Args:
            caplog: the built-in pytest fixture.
        """
        # use temporary config
        config.database.file = self.COBIB_TEST_DIR / "database.yaml"
        config.database.git = True

        # initialize git-tracking
        os.makedirs(self.COBIB_TEST_DIR, exist_ok=True)
        open(  # pylint: disable=consider-using-with
            config.database.file, "w", encoding="utf-8"
        ).close()
        os.system("git init " + str(self.COBIB_TEST_DIR))

        try:
            super().test_handle_argument_error(caplog)
        finally:
            # clean up file system
            rmtree(self.COBIB_TEST_DIR_GIT)
            # clean up config
            config.defaults()

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_tui(self, setup: Any) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            assert "example_multi_file_entry" in screen.display[1]

            expected_log = [
                ("cobib.commands.redo", 10, "Redo command triggered from TUI."),
                ("cobib.commands.redo", 10, "Starting Redo command."),
                ("cobib.commands.redo", 10, "Obtaining git log."),
            ]
            # we only assert the first three messages because the following ones will contain always
            # changing commit SHAs
            assert [log for log in logs if log[0] == "cobib.commands.redo"][0:3] == expected_log

        AddCommand().execute(["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
        UndoCommand().execute([])
        self.run_tui("r", assertion, {})

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_pre_redo_command(self, setup: Any) -> None:
        """Tests the PreRedoCommand event."""

        @Event.PreRedoCommand.subscribe
        def hook(largs: Namespace) -> None:
            print("Hello world!")

        assert Event.PreRedoCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            with pytest.raises(SystemExit):
                RedoCommand().execute([])

            assert out.getvalue() == "Hello world!\n"

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_post_redo_command(self, setup: Any) -> None:
        """Tests the PostRedoCommand event."""

        @Event.PostRedoCommand.subscribe
        def hook(root: Path, sha: str) -> None:
            print(root)

        assert Event.PostRedoCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            AddCommand().execute(["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
            UndoCommand().execute([])

            if Database().get("example_multi_file_entry", None) is not None:
                pytest.skip("UndoCommand failed. No point in attempting Redo.")

            RedoCommand().execute([])

            self._assert()

            assert out.getvalue() == f"{self.COBIB_TEST_DIR}\n"
