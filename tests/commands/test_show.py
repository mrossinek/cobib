"""Tests for coBib's ShowCommand."""

from __future__ import annotations

from itertools import zip_longest
from typing import TYPE_CHECKING, Any

import pytest
from rich.syntax import Syntax
from typing_extensions import override

from cobib.commands import ShowCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import get_resource
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestShowCommand(CommandTest):
    """Tests for coBib's ShowCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ShowCommand

    def _assert(self, output: list[str]) -> None:
        """Common assertion utility method.

        Args:
            output: the actual output of the command.
        """
        with open(get_resource("example_literature.bib"), "r", encoding="utf-8") as expected:
            # we use zip_longest to ensure that we don't have more than we expect
            for line, truth in zip_longest(output, expected):
                if not line:
                    continue
                assert line == truth.strip("\n")

    def test_command(self, setup: Any) -> None:  # type: ignore[explicit-override,override]
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = ShowCommand("einstein")
        cmd.execute()
        self._assert(cmd.entry_str.split("\n"))

    @pytest.mark.parametrize("config_overwrite", [True, False])
    def test_umlaut(self, setup: Any, config_overwrite: bool) -> None:
        """Test the handling of non-ASCII characters.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            config_overwrite: what to overwrite `config.commands.show.encode_latex` with.
        """
        config.commands.show.encode_latex = config_overwrite

        with open(
            get_resource("example_entry_umlaut.yaml", "database"), "r", encoding="utf-8"
        ) as multi_file_entry:
            with open(config.database.file, "a", encoding="utf-8") as database:
                database.write(multi_file_entry.read())
        Database().read()

        cmd = ShowCommand("LaTeX_Einfuhrung")
        cmd.execute()

        expected = [
            "@book{LaTeX_Einfuhrung,",
            " author = {Mustermann, Max and Müller, Mara},",
            ' title = {LaTeX Einf{\\"u}hrung}',
            "}",
        ]
        if config_overwrite:
            expected[1] = ' author = {Mustermann, Max and M{\\"u}ller, Mara},'

        for line, truth in zip_longest(cmd.entry_str.split("\n"), expected):
            if not line:
                continue
            assert line == truth.strip("\n")

    def test_render_porcelain(self, setup: Any) -> None:
        """Test the porcelain rendering.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = ShowCommand("einstein")
        cmd.execute()
        out = cmd.render_porcelain()
        self._assert(out)

    def test_render_rich(self, setup: Any) -> None:
        """Test the rich rendering.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = ShowCommand("einstein")
        cmd.execute()
        renderable = cmd.render_rich()
        assert isinstance(renderable, Syntax)
        assert renderable.code == cmd.entry_str

        assert renderable._lexer == "bibtex"

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        ShowCommand("dummy").execute()
        assert (
            "cobib.commands.show",
            40,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

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
        await self.run_module(monkeypatch, "main", ["cobib", "show", "einstein"])
        self._assert(capsys.readouterr().out.strip().split("\n"))

    def test_event_pre_show_command(self, setup: Any) -> None:
        """Tests the PreShowCommand event."""

        @Event.PreShowCommand.subscribe
        def hook(command: ShowCommand) -> None:
            command.largs.label = "einstein"

        assert Event.PreShowCommand.validate()

        cmd = ShowCommand("knuthwebsite")
        cmd.execute()
        out = cmd.render_porcelain()
        self._assert(out)

    def test_event_post_show_command(self, setup: Any) -> None:
        """Tests the PostShowCommand event."""

        @Event.PostShowCommand.subscribe
        def hook(command: ShowCommand) -> None:
            command.entry_str = "Hello world!"

        assert Event.PostShowCommand.validate()

        cmd = ShowCommand("knuthwebsite")
        cmd.execute()
        out = cmd.render_porcelain()
        assert out == ["Hello world!"]
