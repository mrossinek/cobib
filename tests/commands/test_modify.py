"""Tests for coBib's ModifyCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Type

import pytest

from cobib.commands import ModifyCommand
from cobib.database import Database

from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestModifyCommand(CommandTest, TUITest):
    """Tests for coBib's ModifyCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        """Get the command tested by this class."""
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
            ["tags:test", ["++ID", "einstein"], False],
        ],
    )
    def test_command(
        self, setup: Any, modification: str, filters: List[str], selection: bool
    ) -> None:
        """Test the command itself."""
        git = setup.get("git", False)

        # modify some data
        args = [modification, "--"] + filters
        if selection:
            args = ["-s"] + args

        ModifyCommand().execute(args)

        assert Database()["einstein"].data["tags"] == "test"

        if git:
            # assert the git commit message
            self.assert_git_commit_message(
                "modify",
                {
                    "append": False,
                    "selection": selection,
                    "modification": modification.split(":"),
                    "filter": filters,
                },
            )

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
        ],
        indirect=["setup"],
    )
    def test_append_mode(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test command's append mode."""
        args = ["-a", "tags:test", "--", "++ID", "einstein"]

        with pytest.raises(SystemExit):
            ModifyCommand().execute(args)

        assert (
            "cobib.commands.modify",
            30,
            "The append-mode of the `modify` command has not been implemented yet.",
        ) in caplog.record_tuples

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label."""
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
            [["tags:test", "--", "++ID", "einstein"]],
        ],
    )
    # other variants are already covered by test_command
    def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch, args: List[str]) -> None:
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, "main", ["cobib", "modify"] + args)
        assert Database()["einstein"].data["tags"] == "test"

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "mtags:test -- ++ID knuthwebsite\n\n"],
            [True, "vmtags:test\n\n"],
        ],
    )
    def test_tui(self, setup: Any, select: bool, keys: str) -> None:
        """Test the TUI access of the command."""

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

            assert screen.display[-1].strip() == "'knuthwebsite' was modified."

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
