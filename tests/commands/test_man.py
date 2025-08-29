"""Tests for coBib's ManCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from rich.markdown import Markdown
from rich.tree import Tree
from typing_extensions import override

from cobib.commands import ManCommand
from cobib.config import Event
from cobib.man import manual

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestManCommand(CommandTest):
    """Tests for coBib's ManCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ManCommand

    def test_command(self, setup: Any) -> None:  # type: ignore[override]
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = ManCommand("cobib.1")
        cmd.execute()
        with open(manual.path_from_name("cobib.1")) as file:
            assert cmd.contents == file.read()

    @pytest.mark.parametrize(
        ["input", "expected"],
        [
            ("cobib.1", "cobib.1"),
            ("cobib(1)", "cobib.1"),
            ("config", "cobib-config.5"),
            ("event", "cobib-event.7"),
            ("git", "cobib-git.1"),
            ("git.7", "cobib-git.7"),
        ],
    )
    def test_page_resolution(self, input: str, expected: str) -> None:
        """Test the man-page identification.

        Args:
            input: the input.
            expected: the expected page.
        """
        cmd = ManCommand(input)
        cmd.execute()
        assert cmd.largs.page == expected

    def test_render_porcelain(self, setup: Any) -> None:
        """Test the porcelain rendering.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = ManCommand("cobib.1")
        cmd.execute()
        out = cmd.render_porcelain()
        with open(manual.path_from_name("cobib.1")) as file:
            assert out == file.read().split("\n")

    def test_render_rich(self, setup: Any) -> None:
        """Test the rich rendering.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = ManCommand("cobib.1")
        cmd.execute()
        renderable = cmd.render_rich()
        assert isinstance(renderable, Markdown)

    @pytest.mark.parametrize("porcelain", [False, True])
    def test_index(self, setup: Any, porcelain: bool) -> None:
        """Test the man-page index.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            porcelain: whether to render in porcelain mode.
        """
        cmd = ManCommand()
        cmd.execute()
        renderable = cmd.render_porcelain() if porcelain else cmd.render_rich()
        assert porcelain or isinstance(renderable, Tree)

    @pytest.mark.asyncio
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "-p", "man", "cobib.1"])
        out = capsys.readouterr().out.strip().split("\n")
        with open(manual.path_from_name("cobib.1")) as file:
            assert out == file.read().strip().split("\n")

    def test_event_pre_man_command(self, setup: Any) -> None:
        """Tests the PreManCommand event."""

        @Event.PreManCommand.subscribe
        def hook(command: ManCommand) -> None:
            command.largs.page = "cobib.1"

        assert Event.PreManCommand.validate()

        cmd = ManCommand("config.5")
        cmd.execute()
        out = cmd.render_porcelain()
        with open(manual.path_from_name("cobib.1")) as file:
            assert out == file.read().split("\n")

    def test_event_post_man_command(self, setup: Any) -> None:
        """Tests the PostManCommand event."""

        @Event.PostManCommand.subscribe
        def hook(command: ManCommand) -> None:
            command.contents = "Hello world!"

        assert Event.PostManCommand.validate()

        cmd = ManCommand("cobib.1")
        cmd.execute()
        out = cmd.render_porcelain()
        assert out == ["Hello world!"]
