"""Tests for coBib's InitCommand."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import InitCommand
from cobib.config import Event, config

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestInitCommand(CommandTest):
    """Tests for coBib's InitCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return InitCommand

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False, "database": False}],
            [{"git": True, "database": False}],
            [{"git": True, "database": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(["safe"], [[False], [True]])
    def test_command(self, setup: Any, safe: bool) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            safe: whether the safety of the `InitCommand` should be checked.
        """
        if safe:
            # fill database file
            with open(config.database.file, "w", encoding="utf-8") as file:
                file.write("test")
        # store current time
        now = float(datetime.now().timestamp())
        # try running init
        if setup["git"]:
            InitCommand("--git").execute()
        else:
            InitCommand().execute()
        if safe:
            # check database file still contains 'test'
            with open(config.database.file, "r", encoding="utf-8") as file:
                assert file.read() == "test"
        else:
            # check creation time of temporary database file
            ctime = Path(config.database.file).stat().st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
        if setup["git"] and not setup["database"]:
            # check creation time of temporary database git folder
            ctime = self.COBIB_TEST_DIR_GIT.stat().st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
            # and assert that it is indeed a folder
            assert self.COBIB_TEST_DIR_GIT.is_dir()
            # assert the git commit message
            self.assert_git_commit_message("init", {"git": True})

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False, "database": False}],
        ],
        indirect=["setup"],
    )
    def test_warn_insufficient_config(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning in case of insufficient config.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        try:
            # store current time
            now = float(datetime.now().timestamp())
            # try running init
            InitCommand("--git").execute()

            # assert warning is printed
            assert (
                "cobib.commands.init",
                30,
                "You are about to initialize the git tracking of your database, but this will only "
                "have effect if you also enable the DATABASE/git setting in your configuration "
                "file!",
            ) in caplog.record_tuples
            # now assert that the command did everything as usual though

            # check creation time of temporary database file
            ctime = Path(config.database.file).stat().st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
            # check creation time of temporary database git folder
            ctime = self.COBIB_TEST_DIR_GIT.stat().st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
            # and assert that it is indeed a folder
            assert self.COBIB_TEST_DIR_GIT.is_dir()
            # assert the git commit message
            self.assert_git_commit_message("init", {"git": True})
        finally:
            # clean up file system
            rmtree(self.COBIB_TEST_DIR_GIT)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False, "database": False}],
        ],
        indirect=["setup"],
    )
    # other variants are already covered by test_command
    async def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        # store current time
        now = float(datetime.now().timestamp())
        # try calling init
        await self.run_module(monkeypatch, "main", ["cobib", "init"])
        # try running init
        # check creation time of temporary database file
        ctime = Path(config.database.file).stat().st_ctime
        # assert these times are close
        assert ctime - now < 0.1 or now - ctime < 0.1

    def test_event_pre_init_command(self, setup: Any) -> None:
        """Tests the PreInitCommand event."""

        @Event.PreInitCommand.subscribe
        def hook(command: InitCommand) -> None:
            command.largs.git = True

        assert Event.PreInitCommand.validate()

        InitCommand().execute()

        self.assert_git_commit_message("init", {"git": True})

    def test_event_post_init_command(self, setup: Any) -> None:
        """Tests the PostInitCommand event."""

        @Event.PostInitCommand.subscribe
        def hook(command: InitCommand) -> None:
            command.file.unlink()

        assert Event.PostInitCommand.validate()

        InitCommand().execute()

        assert not (self.COBIB_TEST_DIR_GIT / "literature.yaml").exists()
