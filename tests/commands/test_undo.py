"""Tests for coBib's UndoCommand."""

from __future__ import annotations

import contextlib
import logging
import subprocess
from io import StringIO
from shutil import rmtree
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import AddCommand, UndoCommand
from cobib.config import Event
from cobib.database import Database

from .. import get_resource
from .command_test import CommandTest

EXAMPLE_MULTI_FILE_ENTRY_BIB = get_resource("example_multi_file_entry.bib", "commands")

if TYPE_CHECKING:
    import cobib.commands


class TestUndoCommand(CommandTest):
    """Tests for coBib's UndoCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return UndoCommand

    def _assert(self) -> None:
        """Common assertion utility method."""
        assert Database().get("example_multi_file_entry", None) is None

        # get last commit message
        with subprocess.Popen(
            ["git", "-C", self.COBIB_TEST_DIR, "show", "--format=format:%B", "--no-patch", "HEAD"],
            stdout=subprocess.PIPE,
        ) as proc:
            message, _ = proc.communicate()
            # decode it
            split_message = message.decode("utf-8").split("\n")
            # assert subject line
            assert "Undo" in split_message[0]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup", "expected_exit"],
        [
            [{"git": False}, False],
            [{"git": True}, False],
            [{"git": True}, True],
        ],
        indirect=["setup"],
    )
    async def test_command(
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
            UndoCommand().execute()
            for source, level, message in caplog.record_tuples:
                if ("cobib.commands.undo", logging.ERROR) == (
                    source,
                    level,
                ) and "git-tracking" in message:
                    break
            else:
                pytest.fail("No Error logged from UndoCommand.")
        elif expected_exit:
            # Regression test related to #65
            with pytest.raises(SystemExit):
                UndoCommand().execute()
            for source, level, message in caplog.record_tuples:
                if ("cobib.commands.undo", logging.WARNING) == (
                    source,
                    level,
                ) and "Could not find a commit to undo." in message:
                    break
            else:
                pytest.fail("No Error logged from UndoCommand.")
        else:
            await AddCommand("-b", EXAMPLE_MULTI_FILE_ENTRY_BIB).execute()
            UndoCommand().execute()

            self._assert()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_skipping_undone_commits(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test skipping already undone commits.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        await AddCommand("-b", EXAMPLE_MULTI_FILE_ENTRY_BIB).execute()
        await AddCommand("-b", get_resource("example_entry.bib")).execute()
        UndoCommand().execute()
        caplog.clear()

        UndoCommand().execute()
        self._assert()
        assert "Storing undone commit" in caplog.record_tuples[4][2]
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
        UndoCommand().execute()
        for source, level, message in caplog.record_tuples:
            if ("cobib.commands.undo", logging.ERROR) == (
                source,
                level,
            ) and "configured, but not initialized" in message:
                break
        else:
            pytest.fail("No Error logged from UndoCommand.")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    # other variants are already covered by test_command
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
        """
        await AddCommand("-b", EXAMPLE_MULTI_FILE_ENTRY_BIB).execute()
        await self.run_module(monkeypatch, "main", ["cobib", "undo"])

        self._assert()

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_pre_undo_command(self, setup: Any) -> None:
        """Tests the PreUndoCommand event."""

        @Event.PreUndoCommand.subscribe
        def hook(command: UndoCommand) -> None:
            print("Hello world!")

        assert Event.PreUndoCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            with pytest.raises(SystemExit):
                UndoCommand().execute()

            assert out.getvalue() == "Hello world!\n"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    async def test_event_post_undo_command(self, setup: Any) -> None:
        """Tests the PostUndoCommand event."""

        @Event.PostUndoCommand.subscribe
        def hook(command: UndoCommand) -> None:
            print(command.root)

        assert Event.PostUndoCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            await AddCommand("-b", EXAMPLE_MULTI_FILE_ENTRY_BIB).execute()
            UndoCommand().execute()

            self._assert()

            assert out.getvalue() == f"{self.COBIB_TEST_DIR}\n"
