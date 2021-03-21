"""Tests for coBib's DeleteCommand."""
# pylint: disable=no-self-use,unused-argument

import pytest

from cobib.commands import DeleteCommand
from cobib.config import config
from cobib.database import Database

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest


class TestDeleteCommand(CommandTest, TUITest):
    """Tests for coBib's DeleteCommand."""

    def get_command(self):
        """Get the command tested by this class."""
        return DeleteCommand

    def _assert(self, labels):
        """Common assertion utility method."""
        bib = Database()

        for label in labels:
            assert bib.get(label, None) is None

        with open(config.database.file, "r") as file:
            with open(get_resource("example_literature.yaml"), "r") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    assert line == truth
                with pytest.raises(StopIteration):
                    file.__next__()

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["labels", "skip_commit"],
        [
            [["knuthwebsite"], False],
            [["knuthwebsite", "latexcompanion"], False],
            # non-existent labels should not cause any problems (but skip git check)
            [["dummy"], True],
            [["dummy", "knuthwebsite"], False],
        ],
    )
    def test_command(self, setup, labels, skip_commit):
        """Test the command itself."""
        git = setup.get("git", False)

        # delete some data (for testing simplicity we delete the entries from the end)
        DeleteCommand().execute(labels, git)
        self._assert(labels)

        if git and not skip_commit:
            # assert the git commit message
            self.assert_git_commit_message("delete", {"labels": labels})

    @pytest.mark.parametrize(
        ["labels"],
        [
            [["knuthwebsite"]],
            [["knuthwebsite", "latexcompanion"]],
        ],
    )
    # other variants are already covered by test_command
    def test_cmdline(self, setup, monkeypatch, labels):
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, "main", ["cobib", "delete"] + labels)
        self._assert(labels)

    @pytest.mark.parametrize(
        ["select", "keys", "labels"],
        [
            [False, "vjvdq", ["knuthwebsite", "latexcompanion"]],
            [True, "d", ["knuthwebsite"]],
        ],
    )
    def test_tui(self, setup, select, keys, labels):
        """Test the TUI access of the command."""

        def assertion(screen, logs, **kwargs):
            labels = kwargs.get("labels", [])
            self._assert(labels)

            true_log = [log for log in logs if log[0] == "cobib.commands.delete"]

            expected_log = [
                ("cobib.commands.delete", 10, "Delete command triggered from TUI."),
                ("cobib.commands.delete", 10, "Starting Delete command."),
            ]

            assert true_log[0:2] == expected_log

            # we cannot constructed a unique expected log because we do not know in which order the
            # labels are being removed (because the list of labels gets converted from an unordered
            # set)
            for label in labels:
                assert (
                    "cobib.commands.delete",
                    10,
                    f"Attempting to delete entry '{label}'.",
                ) in true_log
                assert (
                    "cobib.commands.delete",
                    20,
                    f"'{label}' was removed from the database.",
                ) in true_log

                # also assert that the label is no longer visible on screen
                assert all(label not in line for line in screen.display[1:-3])

            assert true_log[-1] == (
                "cobib.commands.delete",
                10,
                "Updating list after Delete command.",
            )

        self.run_tui(keys, assertion, {"labels": labels})
