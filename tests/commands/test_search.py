"""Tests for coBib's SearchCommand."""

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
from cobib.utils.regex import HAS_OPTIONAL_REGEX

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestSearchCommand(CommandTest):
    """Tests for coBib's SearchCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return SearchCommand

    @pytest.fixture(autouse=True)
    def auto_setup(self) -> None:
        """Additional setup instructions which will be run automatically for this class of tests."""
        # NOTE: since some of the tests below overwrite some configuration values which affect the
        # defaults of the command arguments, we automatically reset these defaults to align with the
        # default configuration values before every single test
        SearchCommand.init_argparser()

    def _assert(self, output: list[str], expected: list[str]) -> None:
        """Common assertion utility method.

        Args:
            output: the list of lines printed to `sys.stdout`.
            expected: the expected output.
        """
        # we use zip_longest to ensure that we don't have more than we expect
        for line, exp in zip_longest(output, expected):
            assert line == exp

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args", "expected", "config_overwrite"],
        [
            [
                ["einstein"],
                ["einstein::1", "1::@article{einstein,", "1::author = {Einstein, Albert},"],
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
                    "2::author = {Einstein, Albert},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                False,
            ],
            [
                ["einstein", "-i", "-c", "0"],
                ["einstein::2", "1::@article{einstein,", "2::author = {Einstein, Albert},"],
                False,
            ],
            [
                ["einstein", "-i", "-c", "2"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Einstein, Albert},",
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
                    "2::author = {Einstein, Albert},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                True,
            ],
            [
                ["einstein", "-i"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Einstein, Albert},",
                    "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                True,
            ],
            [
                ["einstein", "Elektro"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "1::author = {Einstein, Albert},",
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
                ["einstein::1", "1::@article{einstein,", "1::author = {Einstein, Albert},"],
                True,
            ],
            [
                # tests the --limit option passed on to the ListCommand
                ["19", "-c", "0", "--", "-l", "1"],
                [
                    "einstein::2",
                    "1::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                    "2::year = {1905}",
                ],
                False,
            ],
        ],
    )
    async def test_command(
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
        # NOTE: the following ensures that the changed configuration value gets populated as the
        # default value of the commands argument parser
        SearchCommand.init_argparser()

        cmd = SearchCommand(*args)
        await cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args", "expected", "config_overwrite"],
        [
            [["Körper", "-c", "0"], [], False],
            [
                ["Körper", "-c", "0"],
                [
                    "einstein::1",
                    r"1::title = {Zur Elektrodynamik bewegter K{\"o}rper},",
                ],
                True,
            ],
            [
                ["Körper", "-c", "0", "-l"],
                [
                    "einstein::1",
                    r"1::title = {Zur Elektrodynamik bewegter K{\"o}rper},",
                ],
                False,
            ],
            [["Körper", "-c", "0", "-L"], [], True],
            [
                # combined with --decode-unicode
                ["Korper", "-c", "0", "-l", "-u"],
                [
                    "einstein::1",
                    r"1::title = {Zur Elektrodynamik bewegter K{\"o}rper},",
                ],
                False,
            ],
        ],
    )
    async def test_decode_latex(
        self, setup: Any, args: list[str], expected: list[str], config_overwrite: bool
    ) -> None:
        """Test the `decode_latex` argument and configuration setting.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected: the expected output.
            config_overwrite: what to overwrite `config.commands.search.decode_latex` with.
        """
        config.commands.search.decode_latex = config_overwrite
        # NOTE: the following ensures that the changed configuration value gets populated as the
        # default value of the commands argument parser
        SearchCommand.init_argparser()

        cmd = SearchCommand(*args)
        await cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "setup",
        [
            {
                "git": False,
                "database": True,
                "database_filename": "unified_database.yaml",
                "database_location": "commands",
            },
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["args", "expected", "config_overwrite"],
        [
            [
                ["Pavosevic", "-c", "0"],
                [
                    "Pavosevic2023::1",
                    "1::@unpublished{Pavosevic2023,",
                ],
                False,
            ],
            [
                ["Pavosevic", "-c", "0"],
                [
                    "Pavosevic2023::2",
                    "1::@unpublished{Pavosevic2023,",
                    "2::author = {Pavošević, Fabijan and Tavernelli, Ivano and Rubio, Angel},",
                ],
                True,
            ],
            [
                ["Pavosevic", "-c", "0", "-u"],
                [
                    "Pavosevic2023::2",
                    "1::@unpublished{Pavosevic2023,",
                    "2::author = {Pavošević, Fabijan and Tavernelli, Ivano and Rubio, Angel},",
                ],
                False,
            ],
            [
                ["Pavosevic", "-c", "0", "-U"],
                [
                    "Pavosevic2023::1",
                    "1::@unpublished{Pavosevic2023,",
                ],
                True,
            ],
        ],
    )
    async def test_decode_unicode(
        self, setup: Any, args: list[str], expected: list[str], config_overwrite: bool
    ) -> None:
        """Test the `decode_unicode` argument and configuration setting.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected: the expected output.
            config_overwrite: what to overwrite `config.commands.search.decode_unicode` with.
        """
        config.commands.search.decode_unicode = config_overwrite
        # NOTE: the following ensures that the changed configuration value gets populated as the
        # default value of the commands argument parser
        SearchCommand.init_argparser()

        cmd = SearchCommand(*args)
        await cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    @pytest.mark.skipif(not HAS_OPTIONAL_REGEX, reason="Requires the optional regex dependency.")
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args", "expected", "config_overwrite"],
        [
            [["einstien", "-c", "0", "-z", "1"], [], 0],
            [["einstien", "-c", "0", "-z", "0"], [], 3],
            [
                ["einstien", "-c", "0", "-z", "2"],
                [
                    "einstein::1",
                    "1::@article{einstein,",
                ],
                0,
            ],
            [
                ["einstien", "-c", "0", "-z", "3"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Einstein, Albert},",
                ],
                0,
            ],
            [
                ["einstien", "-c", "0"],
                [
                    "einstein::2",
                    "1::@article{einstein,",
                    "2::author = {Einstein, Albert},",
                ],
                3,
            ],
        ],
    )
    async def test_fuzziness(
        self, setup: Any, args: list[str], expected: list[str], config_overwrite: int
    ) -> None:
        """Test the `fuzziness` argument and configuration setting.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected: the expected output.
            config_overwrite: what to overwrite `config.commands.search.fuzziness` with.
        """
        config.commands.search.fuzziness = config_overwrite
        # NOTE: the following ensures that the changed configuration value gets populated as the
        # default value of the commands argument parser
        SearchCommand.init_argparser()

        cmd = SearchCommand(*args)
        await cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    @pytest.mark.asyncio
    async def test_context_configuration(self, setup: Any) -> None:
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
        await cmd.execute()
        output = cmd.render_porcelain()
        self._assert(
            output,
            [
                "einstein::2",
                "1::@article{einstein,",
                "2::author = {Einstein, Albert},",
                "2::doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                "2::journal = {Annalen der Physik},",
            ],
        )

    @pytest.mark.asyncio
    async def test_render_rich(self, setup: Any) -> None:
        """Test the rich rendering.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        cmd = SearchCommand("einstein", "-i")
        await cmd.execute()
        renderable = cmd.render_rich()

        assert isinstance(renderable, Tree)
        console = Console(record=True)
        console.print(renderable)
        assert console.export_text() == (
            "einstein - 2 matches\n"
            "├── 1\n"
            "│   └── @article{einstein,\n"
            "└── 2\n"
            "    ├──  author = {Einstein, Albert},\n"
            "    └──  doi = {http://dx.doi.org/10.1002/andp.19053221004},\n"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["expected"],
        [
            [["einstein::1", "1::@article{einstein,", "1::author = {Einstein, Albert},"]],
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
        output = capsys.readouterr().out.strip().split("\n")
        assert output[0].strip().startswith("Searching...")
        self._assert(output[1:], expected)

    @pytest.mark.asyncio
    async def test_event_pre_search_command(self, setup: Any) -> None:
        """Tests the PreSearchCommand event."""

        @Event.PreSearchCommand.subscribe
        def hook(command: SearchCommand) -> None:
            command.largs.query = ["einstein"]

        assert Event.PreSearchCommand.validate()

        expected = ["einstein::1", "1::@article{einstein,", "1::author = {Einstein, Albert},"]

        cmd = SearchCommand("knuthwebsite")
        await cmd.execute()
        output = cmd.render_porcelain()
        self._assert(output, expected)

    @pytest.mark.asyncio
    async def test_event_post_search_command(self, setup: Any) -> None:
        """Tests the PostSearchCommand event."""

        @Event.PostSearchCommand.subscribe
        def hook(command: SearchCommand) -> None:
            print(command.hits, [entry.label for entry in command.entries])

        assert Event.PostSearchCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as file:
            cmd = SearchCommand("einstein")
            await cmd.execute()
            output = file.getvalue().splitlines()
            assert output[0].strip().startswith("Searching...")
            assert output[1].strip() == "1 ['einstein']"
