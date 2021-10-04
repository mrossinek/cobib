"""Tests for coBib's SearchCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import contextlib
import re
from argparse import Namespace
from io import StringIO
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, List, Type

import pytest

from cobib.commands import SearchCommand
from cobib.config import Event, config

from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestSearchCommand(CommandTest, TUITest):
    """Tests for coBib's SearchCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return SearchCommand

    def _assert(self, output: List[str], expected: List[str]) -> None:
        """Common assertion utility method.

        Args:
            output: the list of lines printed to `sys.stdout`.
            expected: the expected output.
        """
        # we use zip_longest to ensure that we don't have more than we expect
        for line, exp in zip_longest(output, expected):
            line = line.replace("\x1b", "")
            line = re.sub(r"\[[0-9;]+m", "", line)
            if exp:
                assert exp in line
            if line and not (line.endswith("match") or line.endswith("matches")):
                assert re.match(r"\[[0-9]+\]", line)

    @pytest.mark.parametrize(
        ["args", "expected", "config_overwrite"],
        [
            [
                ["einstein"],
                ["einstein - 1 match", "@article{einstein,", "author = {Albert Einstein},"],
                False,
            ],
            [
                ["einstein", "-i"],
                [
                    "einstein - 2 matches",
                    "@article{einstein,",
                    "author = {Albert Einstein},",
                    "doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                False,
            ],
            [
                ["einstein", "-i", "-c", "0"],
                ["einstein - 2 matches", "@article{einstein,", "author = {Albert Einstein},"],
                False,
            ],
            [
                ["einstein", "-i", "-c", "2"],
                [
                    "einstein - 2 matches",
                    "@article{einstein,",
                    "author = {Albert Einstein},",
                    "doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                    "journal = {Annalen der Physik},",
                ],
                False,
            ],
            [
                ["einstein"],
                [
                    "einstein - 2 matches",
                    "@article{einstein,",
                    "author = {Albert Einstein},",
                    "doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                True,
            ],
            [
                ["einstein", "-i"],
                [
                    "einstein - 2 matches",
                    "@article{einstein,",
                    "author = {Albert Einstein},",
                    "doi = {http://dx.doi.org/10.1002/andp.19053221004},",
                ],
                True,
            ],
        ],
    )
    def test_command(
        self, setup: Any, args: List[str], expected: List[str], config_overwrite: bool
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected: the expected output.
            config_overwrite: what to overwrite `config.commands.search.ignore_case` with.
        """
        config.commands.search.ignore_case = config_overwrite
        file = StringIO()

        SearchCommand().execute(args, out=file)
        self._assert(file.getvalue().split("\n"), expected)

    @pytest.mark.parametrize(
        ["expected"],
        [
            [["einstein - 1 match", "@article{einstein,", "author = {Albert Einstein},"]],
        ],
    )
    # other variants are already covered by test_command
    def test_cmdline(
        self,
        setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        expected: List[str],
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            expected: the expected output.
        """
        self.run_module(monkeypatch, "main", ["cobib", "search", "einstein"])
        self._assert(capsys.readouterr().out.strip().split("\n"), expected)

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "/einstein\n"],
            [True, "Gv/einstein\n"],
        ],
    )
    def test_tui(self, setup: Any, select: bool, keys: str) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            select: whether to use the TUI selection.
            keys: the string of keys to pass to the TUI.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                "einstein - 1 match",
                "[1]     @article{einstein,",
                "[1]      author = {Albert Einstein},",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            expected_log = [
                ("cobib.commands.search", 10, "Search command triggered from TUI."),
                ("cobib.commands.search", 10, "Starting Search command."),
                (
                    "cobib.commands.search",
                    10,
                    "Available entries to search: ['einstein', 'latexcompanion', 'knuthwebsite']",
                ),
                ("cobib.commands.search", 10, "The search will be performed case sensitive"),
                ("cobib.commands.search", 10, 'Entry "einstein" includes 1 hits.'),
                ("cobib.commands.search", 10, "Applying selection highlighting in search results."),
                ("cobib.commands.search", 10, "Populating viewport with search results."),
                ("cobib.commands.search", 10, "Resetting cursor position to top."),
            ]
            assert [log for log in logs if log[0] == "cobib.commands.search"] == expected_log

            colors = []
            for _ in range(3):
                # color matrix is initialized with default values for three lines
                colors.append([("default", "default")] * 80)

            # selection must be visible
            if select:
                colors[0][0:8] = [("white", "magenta")] * 8
            else:
                colors[0][0:8] = [("blue", "black")] * 8
            # the current line highlighting is only visible from here onward
            colors[0][8:] = [("white", "cyan")] * 72
            # the search keyword highlighting
            colors[1][17:25] = [("red", "black")] * 8
            for idx, color_line in enumerate(colors):
                assert [(c.fg, c.bg) for c in screen.buffer[idx + 1].values()] == color_line

        self.run_tui(keys, assertion, {"selection": select})

    def test_tui_no_hits(self, setup: Any) -> None:
        """Test how the TUI handles no search results.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                "knuthwebsite    Knuth: Computers and Typesetting",
                r"latexcompanion  The \LaTeX\ Companion",
                r"einstein        Zur Elektrodynamik bewegter K{\"o}rper",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            assert "No search hits for 'dummy'!" in screen.display[-1]

            expected_log = [
                ("cobib.commands.search", 10, "Search command triggered from TUI."),
                ("cobib.commands.search", 10, "Starting Search command."),
                (
                    "cobib.commands.search",
                    10,
                    "Available entries to search: ['einstein', 'latexcompanion', 'knuthwebsite']",
                ),
                ("cobib.commands.search", 10, "The search will be performed case sensitive"),
                ("cobib.commands.search", 20, "No search hits for 'dummy'!"),
            ]
            assert [log for log in logs if log[0] == "cobib.commands.search"] == expected_log

        self.run_tui("/dummy\n", assertion, {})

    def test_event_pre_search_command(self, setup: Any) -> None:
        """Tests the PreSearchCommand event."""

        @Event.PreSearchCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.query = "einstein"

        assert Event.PreSearchCommand.validate()

        expected = ["einstein - 1 match", "@article{einstein,", "author = {Albert Einstein},"]

        file = StringIO()
        SearchCommand().execute(["knuthwebsite"], out=file)
        self._assert(file.getvalue().split("\n"), expected)

    def test_event_post_search_command(self, setup: Any) -> None:
        """Tests the PostSearchCommand event."""

        @Event.PostSearchCommand.subscribe
        def hook(hits: int, labels: List[str]) -> None:
            print(labels)

        assert Event.PostSearchCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as file:
            SearchCommand().execute(["einstein"])
            out = file.getvalue().split("\n")
            self._assert(out[:-2], [])
            assert out[-2] == "['einstein']"
