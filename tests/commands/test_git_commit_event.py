"""coBib GitCommit event tests."""
# pylint: disable=unused-argument

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import pytest
from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib.commands.base_command import Command
from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class DummyCommand(Command):
    """A dummy command to test the GitCommit events."""

    name = "dummy"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        # pylint: disable=super-init-not-called
        self.largs = argparse.Namespace()

    @override
    @classmethod
    def init_argparser(cls) -> None:
        pass

    def execute(self) -> None:
        """Does nothing but generate a dummy git commit.

        Args:
            args: a sequence of additional arguments used for the execution.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        with open(config.database.file, "a", encoding="utf-8") as file:
            file.write("dummy")

        self.git()


class TestGitCommitEvent(CommandTest):
    """Tests for the automatic git-commit related events."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return DummyCommand

    @override
    def test_command(self) -> None:
        pytest.skip("The dummy command has no actual command.")

    @override
    def test_handle_argument_error(self, caplog: pytest.LogCaptureFixture) -> None:
        pytest.skip("The dummy command has no argument parser.")

    @pytest.mark.parametrize("setup", [{"git": True}], indirect=["setup"])
    def test_event_pre_git_commit(self, setup: Any) -> None:
        """Test the PreGitCommit event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        @Event.PreGitCommit.subscribe
        def hook(msg: str, args: Optional[dict[str, Any]] = None) -> Optional[str]:
            return "Hello world!"

        assert Event.PreGitCommit.validate()

        DummyCommand().execute()

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

        DummyCommand().execute()

        assert not RelPath(config.database.file).path.exists()
