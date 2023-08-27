"""Tests for coBib's SearchCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import contextlib
from io import StringIO
from itertools import zip_longest
from typing import TYPE_CHECKING, Any

import pytest
from rich.console import Console
from rich.tree import Tree
from typing_extensions import override

from cobib.commands import SearchCommand
from cobib.config import Event, config

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestSearchCommand(CommandTest):
    """Tests for coBib's SearchCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return SearchCommand

    def _assert(self, output: list[str], expected: list[str]) -> None:
        """Common assertion utility method.

        Args:
            output: the list of lines printed to `sys.stdout`.
            expected: the expected output.
        """
        # we use zip_longest to ensure that we don't have more than we expect
        for line, exp in zip_longest(output, expected):
            assert line == exp

    @pytest.mark.parametrize(
        ["args", "expected", "config_overwrite"],
        [
            [
                ["einstein"],
                ["einstein::1", "1::@article{einstein,", "1::author = {Albert Einstein},"],
                False,
            ],
            [
                ["einstein", "--", "--label", "einstein"],
                [],
                False,
            ],
            [
                ["einstein", "-i"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Albert Einstein},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                False,
            ],
            [
                ["einstein", "-i", "-c", "0"],
                ["einstein::2", "1::@article{einstein,", "2::author = {Albert Einstein},"],
                False,
            ],
            [
                ["einstein", "-i", "-c", "2"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Albert Einstein},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                    "2::journal = {Annalen der Physik},",
                ],
                False,
            ],
            [
                ["einstein"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Albert Einstein},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                True,
            ],
            [
                ["einstein", "-i"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Albert Einstein},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                True,
            ],
            [
                ["einstein", "Elektro"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "1::author = {Albert Einstein},",
                    "2::pages = {891--921},",
                    r"2::title = {Zur Elektrodynamik bewegter K{\"o}rper},",
                    "2::volume = {322},",
                ],
                False,
            ],
            [
                ["einstein", "Elektro", "--", "--label", "einstein"],
                [],
                False,
            ],
            [
                ["einstein", "-I"],
                ["einstein::1", "1::@article{einstein,", "1::author = {Albert Einstein},"],
                True,
            ],
        ],
    )
    def test_command(
        self, setup: Any, args: list[str], expected: list[str], config_overwrite: bool
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected: the expected output.
            config_overwrite: what to overwrite `config.commands.search.ignore_case` with.
        """
        config.commands.search.ignore_case = config_overwrite

        cmd = SearchCommand(*args)
        cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    def test_context_configuration(self, setup: Any) -> None:
        """Test the `config.commands.search.context` setting.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        config.commands.search.context = 2

        cmd = SearchCommand(
            "einstein",
            "-i",
            "-c",
            "2",
        )
        cmd.execute()
        output = cmd.render_porcelain()
        self._assert(
            output,
            [
                "einstein::2",
                "1::@article{einstein,",
                "2::author = {Albert Einstein},",
                "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                "2::journal = {Annalen der Physik},",
            ],
        )

    def test_render_rich(self, setup: Any) -> None:
        """Test the rich rendering.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = SearchCommand("einstein", "-i")
        cmd.execute()
        renderable = cmd.render_rich()

        assert isinstance(renderable, Tree)
        console = Console(record=True)
        console.print(renderable)
        assert console.export_text() == (
            "einstein - 2 matches\n"
            "├── 1\n"
            "│   └── @article{einstein,\n"
            "└── 2\n"
            "    ├──  author = {Albert Einstein},\n"
            "    └──  doi = {http://dx.doi.org/10.1002/andp.19053221004},\n"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["expected"],
        [
            [["einstein::1", "1::@article{einstein,", "1::author = {Albert Einstein},"]],
        ],
    )
    # other variants are already covered by test_command
    async def test_cmdline(
        self,
        setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        expected: list[str],
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            expected: the expected output.
        """
        await self.run_module(
            monkeypatch, "main", ["cobib", "--porcelain", "search", "--skip-files", "einstein"]
        )
        self._assert(capsys.readouterr().out.strip().split("\n"), expected)

    def test_event_pre_search_command(self, setup: Any) -> None:
        """Tests the PreSearchCommand event."""

        @Event.PreSearchCommand.subscribe
        def hook(command: SearchCommand) -> None:
            command.largs.query = ["einstein"]

        assert Event.PreSearchCommand.validate()

        expected = ["einstein::1", "1::@article{einstein,", "1::author = {Albert Einstein},"]

        cmd = SearchCommand("knuthwebsite")
        cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    def test_event_post_search_command(self, setup: Any) -> None:
        """Tests the PostSearchCommand event."""

        @Event.PostSearchCommand.subscribe
        def hook(command: SearchCommand) -> None:
            print(command.hits, [entry.label for entry in command.entries])

        assert Event.PostSearchCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as file:
            cmd = SearchCommand("einstein")
            cmd.execute()
            assert file.getvalue().strip() == "1 ['einstein']"
