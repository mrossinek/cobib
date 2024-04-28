"""Tests for coBib's GitCommand."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import GitCommand
from cobib.config import Event

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestGitCommand(CommandTest):
    """Tests for coBib's GitCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return GitCommand

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_command(self, setup: Any, capfd: pytest.CaptureFixture[str]) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            capfd: the built-in pytest fixture.
        """
        GitCommand("--version").execute()
        subprocess.run(["git", "--version"], check=False)

        stdout = capfd.readouterr().out.splitlines()
        assert len(stdout) == 2
        assert stdout[0] == stdout[1]

    def test_guard_no_git(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests a proper warning is raised when the git integration was not initialized.

        Args:
            caplog: the built-in pytest fixture.
        """
        GitCommand("--version").execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.git"]
        assert len(true_log) == 1
        assert true_log[0][2].strip(
            "You must enable coBib's git-traccking in order to use the `Git` command."
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capfd: the built-in pytest fixture.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "git", "--version"])
        # we trigger the same line to simplify the testing procedure
        subprocess.run(["git", "--version"], check=False)

        stdout = capfd.readouterr().out.splitlines()
        assert len(stdout) == 2
        assert stdout[0] == stdout[1]

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_pre_git_command(self, setup: Any, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the PreGitCommand event."""

        @Event.PreGitCommand.subscribe
        def hook(command: GitCommand) -> None:
            print(command.largs, file=sys.stderr)

        assert Event.PreGitCommand.validate()

        GitCommand("--help").execute()

        assert "--help" in capsys.readouterr().err

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_post_git_command(self, setup: Any, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the PostGitCommand event."""

        @Event.PostGitCommand.subscribe
        def hook(command: GitCommand) -> None:
            print(command.largs, file=sys.stderr)

        assert Event.PostGitCommand.validate()

        GitCommand("--version").execute()

        assert "--version" in capsys.readouterr().err
