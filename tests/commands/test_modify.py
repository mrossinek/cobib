"""Tests for coBib's ModifyCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import contextlib
import tempfile
from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ModifyCommand
from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestModifyCommand(CommandTest):
    """Tests for coBib's ModifyCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ModifyCommand

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["modification", "filters", "selection"],
        [
            ["tags:test", ["einstein"], True],
            ["tags:test", ["++label", "einstein"], False],
        ],
    )
    @pytest.mark.parametrize("add", [False, True])
    @pytest.mark.parametrize("dry", [False, True])
    def test_command(
        self,
        setup: Any,
        modification: str,
        filters: list[str],
        selection: bool,
        add: bool,
        dry: bool,
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            modification: the modification string to apply.
            filters: the filter arguments for the command.
            selection: whether the filters are of `selection` type.
            add: whether to use append mode.
            dry: whether to run in dry mode.
        """
        git = setup.get("git", False)

        # modify some data
        args = [modification, "--"] + filters
        if selection:
            args = ["-s"] + args

        expected = ["test"]

        if add:
            # first insert something to add to
            ModifyCommand("tags:dummy", "++label", "einstein").execute()
            args = ["-a"] + args
            expected = ["dummy"] + expected

        if dry:
            args.insert(0, "--dry")

        ModifyCommand(*args).execute()

        if dry:
            if add:
                assert Database()["einstein"].data["tags"] == ["dummy"]
            else:
                assert "tags" not in Database()["einstein"].data.keys()
        else:
            assert Database()["einstein"].data["tags"] == expected

        if git:
            try:
                # assert the git commit message
                self.assert_git_commit_message(
                    "modify",
                    {
                        "modification": modification.split(":"),
                        "dry": False,
                        "add": add,
                        "preserve_files": None,
                        "selection": selection,
                        "filter": filters,
                    },
                )
            except AssertionError:
                assert dry

    @pytest.mark.parametrize(
        ["modification", "expected"],
        [
            ["author: and Knuth", "Albert Einstein and Knuth"],
            ["dummy:test", "test"],
            ["number:2", 12],
            ["number:a", "10a"],
        ],
    )
    def test_add_mode(self, setup: Any, modification: str, expected: Any) -> None:
        """Test more cases of the add mode.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            modification: the modification string to apply.
            expected: the expected final `Entry` field.
        """
        # modify some data
        args = ["-a", modification, "++label", "einstein"]

        field, _ = modification.split(":")

        ModifyCommand(*args).execute()

        assert Database()["einstein"].data[field] == expected

    @pytest.mark.parametrize(
        ["modification", "expected"],
        [
            ["pages:{pages.replace('--', '-')}", "891-921"],
            ["year:{year+10}", 1915],
            ["label:{author.split()[1]}{year}", "Einstein1905"],
            ["string:{'à' !a}", "'\\xe0'"],
            ["number:{1.2345:.2}", "1.2"],
            ["dummy:{dummy}", ""],
        ],
    )
    def test_f_string_interpretation(self, setup: Any, modification: str, expected: Any) -> None:
        """Test f-string interpretation.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            modification: the modification string to apply.
            expected: the expected final `Entry` field.
        """
        # modify some data
        args = [modification, "++label", "einstein"]

        field, *_ = modification.split(":")

        ModifyCommand(*args).execute()

        if field != "label":
            assert Database()["einstein"].data[field] == expected
        else:
            assert "eistein" not in Database().keys()
            assert expected in Database().keys()
            assert Database()[expected].label == expected

    @pytest.mark.parametrize("preserve_files", [None, True, False])
    @pytest.mark.parametrize("config_overwrite", [True, False])
    def test_rename_associated_file(
        self, setup: Any, preserve_files: bool, config_overwrite: bool
    ) -> None:
        """Test removing associated files.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            preserve_files: argument to `ModifyCommand`.
            config_overwrite: what to overwrite `config.commands.modify.preserve_files` with.
        """
        config.commands.modify.preserve_files = config_overwrite

        should_preserve = config_overwrite
        if preserve_files is not None:
            should_preserve = preserve_files

        with tempfile.TemporaryDirectory() as tmpdirname:
            path = RelPath(tmpdirname + "/knuthwebsite.pdf")
            open(path.path, "w", encoding="utf-8").close()  # pylint: disable=consider-using-with

            Database()["knuthwebsite"].file = str(path)

            args = ["label:dummy", "-s", "--", "knuthwebsite"]
            if preserve_files is not None:
                args.insert(2, f"--{'' if preserve_files else 'no-'}preserve-files")
            ModifyCommand(*args).execute()
            assert "dummy" in Database().keys()

            target = RelPath(tmpdirname + "/dummy.pdf")
            if should_preserve:
                assert path.path.exists()
            else:
                assert target.path.exists()

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        # Note: when using a filter, no non-existent label can occur
        args = ["-s", "tags:test", "--", "dummy"]
        ModifyCommand(*args).execute()
        assert (
            "cobib.commands.modify",
            30,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["args"],
        [
            [["-s", "tags:test", "--", "einstein"]],
            [["tags:test", "--", "++label", "einstein"]],
        ],
    )
    # other variants are already covered by test_command
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, args: list[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            args: additional arguments to pass to the command.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "modify"] + args)
        assert Database()["einstein"].data["tags"] == ["test"]

    def test_event_pre_modify_command(self, setup: Any) -> None:
        """Tests the PreModifyCommand event."""

        @Event.PreModifyCommand.subscribe
        def hook(command: ModifyCommand) -> None:
            command.largs.modification = ("number", "2")

        assert Event.PreModifyCommand.validate()

        ModifyCommand("-a", "number:3", "++label", "einstein").execute()

        assert Database()["einstein"].data["number"] == 12

    def test_event_post_modify_command(self, setup: Any) -> None:
        """Tests the PostModifyCommand event."""

        @Event.PostModifyCommand.subscribe
        def hook(command: ModifyCommand) -> None:
            print([entry.label for entry in command.modified_entries])

        assert Event.PostModifyCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            ModifyCommand("-a", "number:3", "++label", "einstein").execute()
            assert out.getvalue() == "['einstein']\n"

    def test_hook_last_modified(self, setup: Any) -> None:
        """Tests the hook to keep track of the last time an entry was modified.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        assert "last_modified" not in Database()["einstein"].data

        @Event.PostModifyCommand.subscribe
        def last_modified(command: ModifyCommand) -> None:
            for entry in command.modified_entries:
                entry.data["last_modified"] = str(datetime.now())

        assert Event.PostModifyCommand.validate()

        ModifyCommand("-a", "number:3", "++label", "einstein").execute()

        assert "last_modified" in Database()["einstein"].data
