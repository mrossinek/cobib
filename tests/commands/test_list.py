"""Tests for coBib's ListCommand."""

from __future__ import annotations

import contextlib
from copy import copy
from io import StringIO
from itertools import zip_longest
from typing import TYPE_CHECKING, Any

import pytest
from rich.table import Table
from typing_extensions import override

from cobib.commands import ListCommand
from cobib.config import Event, config

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestListCommand(CommandTest):
    """Tests for coBib's ListCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ListCommand

    @pytest.mark.parametrize(
        ["args", "expected_labels", "config_overwrite"],
        [
            [[], ["einstein", "latexcompanion", "knuthwebsite"], False],
            [["-l", "1"], ["einstein"], False],
            [["-r"], ["knuthwebsite", "latexcompanion", "einstein"], False],
            [["-s", "year"], ["knuthwebsite", "einstein", "latexcompanion"], False],
            [["-r", "-s", "year"], ["latexcompanion", "einstein", "knuthwebsite"], False],
            [["++author", "Einstein"], ["einstein"], False],
            [["++author", "einstein", "-i"], ["einstein"], False],
            [["++author", "einstein", "-I"], [], True],
            [["--author", "Einstein"], ["latexcompanion", "knuthwebsite"], False],
            [["++author", "Einstein", "++author", "Knuth"], [], False],
            [
                ["-x", "++author", "Einstein", "++author", "Knuth"],
                ["einstein", "knuthwebsite"],
                False,
            ],
        ],
    )
    def test_command(
        self, setup: Any, args: list[str], expected_labels: list[str], config_overwrite: bool
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected_labels: the expected list of labels.
            config_overwrite: what to overwrite `config.commands.list_.ignore_case` with.
        """
        config.commands.list_.ignore_case = config_overwrite
        original_default_columns = copy(config.commands.list_.default_columns)

        cmd = ListCommand(*args)
        cmd.execute()
        assert [entry.label for entry in cmd.entries] == expected_labels
        # NOTE: this is a regression test against https://gitlab.com/cobib/cobib/-/issues/117
        assert original_default_columns == config.commands.list_.default_columns

    @pytest.mark.parametrize(
        ["args", "expected_labels", "expected_keys", "config_overwrite"],
        [
            [[], ["einstein", "latexcompanion", "knuthwebsite"], set(), False],
            [["++author", "Einstein"], ["einstein"], {"author"}, False],
            [["++author", "einstein", "-i"], ["einstein"], {"author"}, False],
            [["++author", "einstein", "-I"], [], {"author"}, True],
            [["--author", "Einstein"], ["latexcompanion", "knuthwebsite"], {"author"}, False],
            [["++author", "Einstein", "++author", "Knuth"], [], {"author"}, False],
            [
                ["-x", "++author", "Einstein", "++author", "Knuth"],
                ["einstein", "knuthwebsite"],
                {"author"},
                False,
            ],
        ],
    )
    def test_filter_entries(
        self,
        setup: Any,
        args: list[str],
        expected_labels: list[str],
        expected_keys: set[str],
        config_overwrite: bool,
    ) -> None:
        """Tests the filtering methods.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected_labels: the expected list of labels which match the filter.
            expected_keys: the expected keys which were filtered on.
            config_overwrite: what to overwrite `config.commands.list_.ignore_case` with.
        """
        config.commands.list_.ignore_case = config_overwrite

        filtered_entries, filtered_keys = ListCommand(*args).filter_entries()
        assert filtered_keys == expected_keys
        assert [entry.label for entry in filtered_entries] == expected_labels

    @pytest.mark.parametrize(
        ["args", "expected_labels"],
        [
            [[], ["einstein", "latexcompanion", "knuthwebsite"]],
            [["-r"], ["knuthwebsite", "latexcompanion", "einstein"]],
            [["-s", "year"], ["knuthwebsite", "einstein", "latexcompanion"]],
            [["-r", "-s", "year"], ["latexcompanion", "einstein", "knuthwebsite"]],
            [["-r", "--author", "Einstein"], ["knuthwebsite", "latexcompanion"]],
            [["-s", "year", "--author", "Einstein"], ["knuthwebsite", "latexcompanion"]],
            [["-r", "-s", "year", "--author", "Einstein"], ["latexcompanion", "knuthwebsite"]],
        ],
    )
    def test_sort_entries(self, setup: Any, args: list[str], expected_labels: list[str]) -> None:
        """Tests the sorting methods.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected_labels: the expected list of labels which match the filter.
        """
        cmd = ListCommand(*args)
        # NOTE: if we do not call `Entry.filter_entries` first, the list of labels will be empty!
        _, _ = cmd.filter_entries()
        sorted_entries = cmd.sort_entries()
        assert [entry.label for entry in sorted_entries] == expected_labels

    @pytest.mark.parametrize(
        ["args", "expected_labels", "expected_keys"],
        [
            [
                ["-r", "-s", "year", "-l", "1", "--author", "Einstein"],
                ["latexcompanion"],
                {"author"},
            ],
        ],
    )
    def test_execute_dull(
        self,
        setup: Any,
        args: list[str],
        expected_labels: list[str],
        expected_keys: set[str],
    ) -> None:
        """Tests the `ListCommand.execute_dull` method.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected_labels: the expected list of labels which match the filter.
            expected_keys: the expected keys which were filtered on.
        """
        final_entries, filtered_keys = ListCommand(*args).execute_dull()
        assert filtered_keys == expected_keys
        assert [entry.label for entry in final_entries] == expected_labels

    def test_missing_keys(self, setup: Any) -> None:
        """Asserts issue #1 is fixed.

        When a key is queried which is not present in all entries, the list command should return
        normally.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        filtered_entries, filtered_keys = ListCommand("++year", "1905").filter_entries()
        assert [entry.label for entry in filtered_entries] == ["einstein"]
        assert filtered_keys == {"year"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "expected",
        [
            [
                ["label", "title"],
                ["einstein", r"Zur Elektrodynamik bewegter K{\"o}rper"],
                ["latexcompanion", r"The \LaTeX\ Companion"],
                ["knuthwebsite", "Knuth: Computers and Typesetting"],
            ],
        ],
    )
    # other variants are already covered by test_command
    async def test_cmdline(
        self,
        setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        expected: list[list[str]],
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            expected: the expected list of labels.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "--porcelain", "list"])
        stdout = capsys.readouterr().out.strip().split("\n")
        for line, truth in zip_longest(stdout, expected):
            assert line.split("::") == truth

    @pytest.mark.parametrize(
        ["args", "expected_cols", "expected_rows"],
        [
            [[], ["label", "title"], ["einstein", "latexcompanion", "knuthwebsite"]],
            [["-r"], ["label", "title"], ["knuthwebsite", "latexcompanion", "einstein"]],
            [
                ["-s", "year"],
                ["label", "title", "year"],
                ["knuthwebsite", "einstein", "latexcompanion"],
            ],
            [
                ["-r", "-s", "year"],
                ["label", "title", "year"],
                ["latexcompanion", "einstein", "knuthwebsite"],
            ],
            [["++author", "Einstein"], ["label", "title", "author"], ["einstein"]],
            [
                ["--author", "Einstein"],
                ["label", "title", "author"],
                ["latexcompanion", "knuthwebsite"],
            ],
            [["++author", "Einstein", "++author", "Knuth"], ["label", "title", "author"], []],
            [
                ["-x", "++author", "Einstein", "++author", "Knuth"],
                ["label", "title", "author"],
                ["einstein", "knuthwebsite"],
            ],
        ],
    )
    def test_render_rich(
        self, setup: Any, args: list[str], expected_cols: list[str], expected_rows: list[str]
    ) -> None:
        """Test the `render_rich` method.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
            expected_cols: the expected list of columns.
            expected_rows: the expected list of row entries.
        """
        cmd = ListCommand(*args)
        cmd.execute()
        renderable = cmd.render_rich()

        assert isinstance(renderable, Table)
        assert [col.header for col in renderable.columns] == expected_cols
        assert len(renderable.rows) == len(expected_rows)

        assert renderable.columns[0]._cells == expected_rows

    def test_event_pre_list_command(self, setup: Any) -> None:
        """Tests the PreListCommand event."""

        @Event.PreListCommand.subscribe
        def hook(command: ListCommand) -> None:
            command.largs.author = None

        assert Event.PreListCommand.validate()

        cmd = ListCommand("++author", "Einstein")
        cmd.execute()

        assert [entry.label for entry in cmd.entries] == [
            "einstein",
            "latexcompanion",
            "knuthwebsite",
        ]

    def test_event_post_list_command(self, setup: Any) -> None:
        """Tests the PostListCommand event."""

        @Event.PostListCommand.subscribe
        def hook(command: ListCommand) -> None:
            print([entry.label for entry in command.entries], command.columns)

        assert Event.PostListCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            cmd = ListCommand()
            cmd.execute()

            assert (
                out.getvalue()
                == "['einstein', 'latexcompanion', 'knuthwebsite'] ['label', 'title']\n"
            )
