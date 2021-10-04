"""Tests for coBib's ListCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import contextlib
import os
from argparse import Namespace
from io import StringIO
from itertools import zip_longest
from shutil import copyfile
from typing import TYPE_CHECKING, Any, List, Type

import pytest

from cobib.commands import ListCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestListCommand(CommandTest, TUITest):
    """Tests for coBib's ListCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return ListCommand

    @pytest.mark.parametrize(
        ["args", "expected"],
        [
            [[], ["einstein", "latexcompanion", "knuthwebsite"]],
            [["-r"], ["knuthwebsite", "latexcompanion", "einstein"]],
            [["-s", "year"], ["knuthwebsite", "einstein", "latexcompanion"]],
            [["-r", "-s", "year"], ["latexcompanion", "einstein", "knuthwebsite"]],
            [["++author", "Einstein"], ["einstein"]],
            [["--author", "Einstein"], ["latexcompanion", "knuthwebsite"]],
            [["++author", "Einstein", "++author", "Knuth"], []],
            [["-x", "++author", "Einstein", "++author", "Knuth"], ["einstein", "knuthwebsite"]],
        ],
    )
    def test_command(self, setup: Any, args: List[str], expected: List[str]) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected: the expected list of labels.
        """
        # redirect output of list to string
        file = StringIO()
        tags = ListCommand().execute(args, out=file)
        assert tags == expected
        # TODO: actually do more assertion on the table output (awaiting ListCommand refactoring)
        for line in file.getvalue().split("\n"):
            if line.startswith("label") or all(c in "- " for c in line):
                # skip table header
                continue
            assert line.split()[0] in expected

    def test_missing_keys(self, setup: Any) -> None:
        """Asserts issue #1 is fixed.

        When a key is queried which is not present in all entries, the list command should return
        normally.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        # redirect output of list to string
        file = StringIO()
        tags = ListCommand().execute(["++year", "1905"], out=file)
        expected = ["einstein"]
        assert tags == expected
        for line in file.getvalue().split("\n"):
            if line.startswith("label") or all(c in "- " for c in line):
                # skip table header
                continue
            assert line.split()[0] in expected

    @pytest.mark.parametrize(
        ["expected"],
        [
            [["einstein", "latexcompanion", "knuthwebsite"]],
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
            expected: the expected list of labels.
        """
        self.run_module(monkeypatch, "main", ["cobib", "list"])
        for line, truth in zip_longest(capsys.readouterr().out.strip().split("\n"), expected):
            # we wrap the list into an iterator in order to handle an empty list, too
            assert next(iter(line.split()), None) == truth

    def test_tui(self, setup: Any) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                r"knuthwebsite    Knuth: Computers and Typesetting",
                r"latexcompanion  The \LaTeX\ Companion",
                r"einstein        Zur Elektrodynamik bewegter K{\"o}rper",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()
            expected_log = [
                ("cobib.commands.list", 10, "Starting List command."),
                ("cobib.commands.list", 10, "Gathering possible filter arguments."),
                ("cobib.commands.list", 10, "Constructing filter."),
                ("cobib.commands.list", 10, "Final filter configuration: {}"),
                ("cobib.commands.list", 10, 'Entry "einstein" matches the filter.'),
                ("cobib.commands.list", 10, 'Entry "latexcompanion" matches the filter.'),
                ("cobib.commands.list", 10, 'Entry "knuthwebsite" matches the filter.'),
                ("cobib.commands.list", 10, "Column widths determined to be: [14, 38]"),
                ("cobib.commands.list", 10, "Reversing order."),
            ]
            assert [log for log in logs if log[0] == "cobib.commands.list"] == expected_log

        self.run_tui("", assertion, {})

    @pytest.mark.parametrize(
        ["keys"],
        [
            ["sauthor\n"],
            ["syear\nsauthor\n"],
        ],
    )
    def test_tui_sort(self, setup: Any, keys: str) -> None:
        """Test the TUI `sort` command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            keys: the string of keys to pass to the TUI.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                "latexcompanion  Michel Goossens and Frank Mittelbach and Alexander Samarin  The",
                "knuthwebsite    Donald Knuth                                                Knut",
                "einstein        Albert Einstein                                             Zur",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()
            expected_log = [
                ("cobib.commands.list", 10, "List command triggered from TUI."),
                ("cobib.commands.list", 10, "Clearing current buffer contents."),
                ("cobib.commands.list", 10, "Starting List command."),
                ("cobib.commands.list", 10, "Gathering possible filter arguments."),
                ("cobib.commands.list", 10, "Constructing filter."),
                ("cobib.commands.list", 10, "Final filter configuration: {}"),
                ("cobib.commands.list", 10, 'Sorting by "author".'),
                ("cobib.commands.list", 10, 'Entry "einstein" matches the filter.'),
                ("cobib.commands.list", 10, 'Entry "latexcompanion" matches the filter.'),
                ("cobib.commands.list", 10, 'Entry "knuthwebsite" matches the filter.'),
                ("cobib.commands.list", 10, "Column widths determined to be: [14, 58, 38]"),
                ("cobib.commands.list", 10, "Sorting table in reverse order."),
                (
                    "cobib.commands.list",
                    10,
                    "Post-process ListCommand arguments for consistent prompt.",
                ),
                ("cobib.commands.list", 10, 'Using sort argument: "author"'),
                ("cobib.commands.list", 10, "Populating buffer with ListCommand results."),
            ]
            true_log = [log for log in logs if log[0] == "cobib.commands.list"]
            try:
                for log, truth in zip(true_log[true_log.index(expected_log[0]) :], expected_log):
                    assert log == truth
            except AssertionError:
                # in the second parametrized test we simply check that the previous sort label was
                # removed correctly
                for msg in [
                    'Sorting by "year".',
                    'Removing previous sort argument: "year"',
                    'Sorting by "author".',
                ]:
                    assert ("cobib.commands.list", 10, msg) in true_log

        self.run_tui(keys, assertion, {})

    @pytest.mark.parametrize(
        ["keys"],
        [
            ["f++label einstein\n"],
            ["f++label knuthwebsite\nf\b\b\b\b\b\b\b\b\b\b\b\b\beinstein\n"],
        ],
    )
    def test_tui_filter(self, setup: Any, keys: str) -> None:
        """Test the TUI `filter` command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            keys: the string of keys to pass to the TUI.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                r"einstein  Zur Elektrodynamik bewegter K{\"o}rper",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()
            expected_log = [
                ("cobib.commands.list", 10, "List command triggered from TUI."),
                ("cobib.commands.list", 10, "Clearing current buffer contents."),
                ("cobib.commands.list", 10, "Starting List command."),
                ("cobib.commands.list", 10, "Gathering possible filter arguments."),
                ("cobib.commands.list", 10, "Constructing filter."),
                (
                    "cobib.commands.list",
                    10,
                    "Final filter configuration: {('label', True): ['einstein']}",
                ),
                ("cobib.commands.list", 10, 'Entry "einstein" matches the filter.'),
                ("cobib.commands.list", 10, "Column widths determined to be: [8, 38]"),
                ("cobib.commands.list", 10, "Reversing order."),
                (
                    "cobib.commands.list",
                    10,
                    "Post-process ListCommand arguments for consistent prompt.",
                ),
                ("cobib.commands.list", 10, 'Adding filter to prompt: "++label einstein"'),
                ("cobib.commands.list", 10, "Populating buffer with ListCommand results."),
            ]
            true_log = [log for log in logs if log[0] == "cobib.commands.list"]
            try:
                for log, truth in zip(true_log[true_log.index(expected_log[0]) :], expected_log):
                    assert log == truth
            except AssertionError:
                # in the second parametrized test we simply check that the previous filters were
                # removed correctly
                for msg in [
                    "Final filter configuration: {('label', True): ['knuthwebsite']}",
                    'Adding filter to prompt: "++label knuthwebsite"',
                    'Removing filter from prompt: "++label knuthwebsite"',
                    "Final filter configuration: {('label', True): ['einstein']}",
                    'Adding filter to prompt: "++label einstein"',
                ]:
                    assert ("cobib.commands.list", 10, msg) in true_log

        self.run_tui(keys, assertion, {})

    @pytest.mark.parametrize(
        ["keys", "messages"],
        [
            ["s\b\b\b\b\b\b\n", ['Removing "reverse" list argument.']],
            ["s\b\b\b\b\b\b\ns\b\b\b-r\n", ['Adding "reverse" list argument.']],
            ["f++label einstein -x\n", ['Adding "OR" list argument.']],
            ["f-x\nf\b\b\b\b\b\b\b\n", ['Removing "OR" list argument.']],
        ],
    )
    def test_tui_argument_unification(self, setup: Any, keys: str, messages: List[str]) -> None:
        """Test that the TUI unifies keyword arguments.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            keys: the string of keys to pass to the TUI.
            messages: the expected list of log messages.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            true_log = [log for log in logs if log[0] == "cobib.commands.list"]
            for msg in messages:
                assert ("cobib.commands.list", 10, msg) in true_log

        self.run_tui(keys, assertion, {})

    # manually overwrite this test because we must populate the database with actual data
    def test_handle_argument_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of ArgumentError.

        Args:
            caplog: the built-in pytest fixture.
        """
        # use temporary config
        config.database.file = self.COBIB_TEST_DIR / "database.yaml"
        config.database.git = True

        # load temporary database
        os.makedirs(self.COBIB_TEST_DIR, exist_ok=True)
        copyfile(get_resource("example_literature.yaml"), config.database.file)
        Database().read()

        try:
            super().test_handle_argument_error(caplog)
        finally:
            # clean up file system
            os.remove(config.database.file)
            # clean up database
            Database().clear()
            # clean up config
            config.defaults()

    def test_event_pre_list_command(self, setup: Any) -> None:
        """Tests the PreListCommand event."""

        @Event.PreListCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.author = None

        assert Event.PreListCommand.validate()

        expected = [
            'einstein        Zur Elektrodynamik bewegter K{\\"o}rper',
            "latexcompanion  The \\LaTeX\\ Companion",
            "knuthwebsite    Knuth: Computers and Typesetting",
        ]

        with contextlib.redirect_stdout(StringIO()) as out:
            ListCommand().execute(["++author", "Einstein"])

            for truth, exp in zip(out.getvalue().split("\n"), expected):
                assert truth.strip() == exp

    def test_event_post_list_command(self, setup: Any) -> None:
        """Tests the PostListCommand event."""

        @Event.PostListCommand.subscribe
        def hook(labels: List[str]) -> None:
            print(labels)

        assert Event.PostListCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            ListCommand().execute([])

            assert (
                out.getvalue().split("\n")[-2] == "['einstein', 'latexcompanion', 'knuthwebsite']"
            )
