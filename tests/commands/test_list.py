"""Tests for coBib's ListCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import contextlib
import os
from copy import copy
from io import StringIO
from itertools import zip_longest
from shutil import copyfile
from typing import TYPE_CHECKING, Any, List, Set, Type

import pytest
from rich.table import Table
from typing_extensions import override

from cobib.commands import ListCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import get_resource
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestListCommand(CommandTest):
    """Tests for coBib's ListCommand."""

    @override
    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        return ListCommand

    @pytest.mark.parametrize(
        ["args", "expected_labels", "config_overwrite"],
        [
            [[], ["einstein", "latexcompanion", "knuthwebsite"], False],
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
        self, setup: Any, args: List[str], expected_labels: List[str], config_overwrite: bool
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
        args: List[str],
        expected_labels: List[str],
        expected_keys: Set[str],
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
        expected: List[List[str]],
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
        self, setup: Any, args: List[str], expected_cols: List[str], expected_rows: List[str]
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
        # pylint: disable=protected-access
        assert renderable.columns[0]._cells == expected_rows

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
        except SystemExit:
            pass
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
