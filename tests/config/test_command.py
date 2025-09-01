"""Tests for coBib's ExampleConfigCommand."""

from __future__ import annotations

from itertools import zip_longest
from typing import TYPE_CHECKING, cast

import pytest
from rich.syntax import Syntax
from typing_extensions import override

from cobib.config import config
from cobib.config.command import ExampleConfigCommand
from tests.commands.command_test import CommandTest

from .. import get_resource

if TYPE_CHECKING:
    import cobib.commands


class TestPrintExampleConfig(CommandTest):
    """Tests for coBib's ExampleConfigCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ExampleConfigCommand

    def _assert(self, out: str) -> None:
        """The utility assertion method.

        Args:
            out: The captured output of the command.
        """
        with open(
            get_resource("example.py", "../src/cobib/config"), "r", encoding="utf-8"
        ) as expected:
            for line, truth in zip_longest(out.split("\n"), expected):
                try:
                    assert line == truth.strip()
                except AttributeError:
                    # an empty string can equal no string (i.e. None)
                    assert bool(line) == bool(truth)

    @override
    def test_command(self) -> None:
        cmd = self.get_command()()
        cmd.execute()
        self._assert("\n".join(cmd.render_porcelain()))

    def test_rich(self) -> None:
        """Tests the rich output."""
        cmd = self.get_command()()
        cmd.execute()
        truth = cast(Syntax, cmd.render_rich())
        with open(
            get_resource("example.py", "../src/cobib/config"), "r", encoding="utf-8"
        ) as expected:
            syntax = Syntax(
                expected.read().strip(),
                "python",
                theme=config.theme.syntax.get_theme(),
                background_color=config.theme.syntax.get_background_color(),
                line_numbers=False,
                word_wrap=False,
            )
            assert syntax.code == truth.code
            assert syntax.background_color == truth.background_color
            assert syntax.word_wrap == truth.word_wrap

    @pytest.mark.asyncio
    async def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await super().run_module(monkeypatch, "main", ["cobib", "-p", "_example_config"])
        self._assert(capsys.readouterr().out)
