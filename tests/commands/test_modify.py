"""Tests for coBib's ModifyCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import contextlib
import tempfile
from argparse import Namespace
from io import StringIO
from typing import TYPE_CHECKING, Any, List, Type

import pytest

from cobib.commands import ModifyCommand
from cobib.config import Event
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestModifyCommand(CommandTest, TUITest):
    """Tests for coBib's ModifyCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
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
        filters: List[str],
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
            ModifyCommand().execute(["tags:dummy", "++label", "einstein"])
            args = ["-a"] + args
            expected = ["dummy"] + expected

        if dry:
            args.insert(0, "--dry")

        ModifyCommand().execute(args)

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
                        "dry": False,
                        "add": add,
                        "selection": selection,
                        "preserve_files": False,
                        "modification": modification.split(":"),
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

        ModifyCommand().execute(args)

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

        ModifyCommand().execute(args)

        if field != "label":
            assert Database()["einstein"].data[field] == expected
        else:
            assert "eistein" not in Database().keys()
            assert expected in Database().keys()
            assert Database()[expected].label == expected

    @pytest.mark.parametrize("preserve_files", [True, False])
    def test_rename_associated_file(self, setup: Any, preserve_files: bool) -> None:
        """Test removing associated files.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            preserve_files: argument to `DeleteCommand`.
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            path = RelPath(tmpdirname + "/knuthwebsite.pdf")
            open(path.path, "w", encoding="utf-8").close()  # pylint: disable=consider-using-with

            Database()["knuthwebsite"].file = str(path)

            args = ["label:dummy", "-s", "--", "knuthwebsite"]
            if preserve_files:
                args.insert(2, "--preserve-files")
            ModifyCommand().execute(args)
            assert "dummy" in Database().keys()

            target = RelPath(tmpdirname + "/dummy.pdf")
            if preserve_files:
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
        ModifyCommand().execute(args)
        assert (
            "cobib.commands.modify",
            30,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

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
    def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch, args: List[str]) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            args: additional arguments to pass to the command.
        """
        self.run_module(monkeypatch, "main", ["cobib", "modify"] + args)
        assert Database()["einstein"].data["tags"] == ["test"]

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "mtags:test -- ++label knuthwebsite\n\n"],
            [True, "vmtags:test\n\n"],
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
                "@misc{knuthwebsite,",
                "author = {Donald Knuth},",
                "tags = {test},",
                "title = {Knuth: Computers and Typesetting},",
                r"url = {http://www-cs-faculty.stanford.edu/\~{}uno/abcde.html}",
                "}",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            expected_log = [
                ("cobib.commands.modify", 10, "Modify command triggered from TUI."),
                ("cobib.commands.modify", 10, "Starting Modify command."),
                ("cobib.commands.modify", 20, "'knuthwebsite' was modified."),
            ]
            if kwargs.get("selection", False):
                expected_log.insert(
                    2,
                    (
                        "cobib.commands.modify",
                        20,
                        "Selection given. Interpreting `filter` as a list of labels",
                    ),
                )
            else:
                expected_log.insert(
                    2,
                    (
                        "cobib.commands.modify",
                        10,
                        "Gathering filtered list of entries to be modified.",
                    ),
                )
            assert [log for log in logs if log[0] == "cobib.commands.modify"] == expected_log

        self.run_tui(keys, assertion, {"selection": select})

    def test_event_pre_modify_command(self, setup: Any) -> None:
        """Tests the PreModifyCommand event."""

        @Event.PreModifyCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.modification = ("number", "2")

        assert Event.PreModifyCommand.validate()

        ModifyCommand().execute(["-a", "number:3", "++label", "einstein"])

        assert Database()["einstein"].data["number"] == 12

    def test_event_post_modify_command(self, setup: Any) -> None:
        """Tests the PostModifyCommand event."""

        @Event.PostModifyCommand.subscribe
        def hook(labels: List[str], dry: bool) -> None:
            print(labels)

        assert Event.PostModifyCommand.validate()

        with contextlib.redirect_stdout(StringIO()) as out:
            ModifyCommand().execute(["-a", "number:3", "++label", "einstein"])

            assert out.getvalue() == "['einstein']\n"
