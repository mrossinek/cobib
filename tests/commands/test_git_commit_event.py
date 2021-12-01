"""coBib GitCommit event tests."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import sys
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Dict, List, Optional, Type

import pytest

from cobib.commands.base_command import Command
from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands
    import cobib.tui


class DummyCommand(Command):
    """A dummy command to test the GitCommit events."""

    name = "dummy"

    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Does nothing but generate a dummy git commit.

        Args:
            args: a sequence of additional arguments used for the execution.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        with open(config.database.file, "a", encoding="utf-8") as file:
            file.write("dummy")

        self.git()

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        pass


class TestGitCommitEvent(CommandTest):
    """Tests for the automatic git-commit related events."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return DummyCommand

    def test_command(self) -> None:
        # noqa: D102
        pytest.skip("The dummy command has no actual command.")

    def test_handle_argument_error(self, caplog: pytest.LogCaptureFixture) -> None:
        # noqa: D102
        pytest.skip("The dummy command has no argument parser.")

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_pre_git_commit(self, setup: Any) -> None:
        """Test the PreGitCommit event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        @Event.PreGitCommit.subscribe
        def hook(msg: str, args: Optional[Dict[str, Any]] = None) -> Optional[str]:
            return "Hello world!"

        assert Event.PreGitCommit.validate()

        DummyCommand().execute([])

        self.assert_git_commit_message("dummy", msg="Hello world!\n")

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_post_git_commit(self, setup: Any) -> None:
        """Test the PostGitCommit event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        @Event.PostGitCommit.subscribe
        def hook(root: Path, file: Path) -> None:
            file.unlink()

        assert Event.PostGitCommit.validate()

        DummyCommand().execute([])

        assert not RelPath(config.database.file).path.exists()
