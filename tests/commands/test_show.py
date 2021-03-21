"""Tests for coBib's ShowCommand."""
# pylint: disable=no-self-use,unused-argument

from io import StringIO
from itertools import zip_longest

import pytest

from cobib.commands import ShowCommand

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest


class TestShowCommand(CommandTest, TUITest):
    """Tests for coBib's ShowCommand."""

    def get_command(self):
        """Get the command tested by this class."""
        return ShowCommand

    def _assert(self, output):
        """Common assertion utility method."""
        with open(get_resource("example_literature.bib"), "r") as expected:
            # we use zip_longest to ensure that we don't have more than we expect
            for line, truth in zip_longest(output, expected):
                if not line:
                    continue
                assert line == truth.strip("\n")

    def test_command(self, setup):
        """Test the command itself."""
        # redirect output of show to string
        file = StringIO()
        ShowCommand().execute(["einstein"], out=file)
        self._assert(file.getvalue().split("\n"))

    def test_warning_missing_label(self, setup, caplog):
        """Test warning for missing label."""
        ShowCommand().execute(["dummy"])
        assert (
            "cobib.commands.show",
            40,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    def test_cmdline(self, setup, monkeypatch, capsys):
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, "main", ["cobib", "show", "einstein"])
        self._assert(capsys.readouterr().out.strip().split("\n"))

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "\n"],
            [True, "v\n"],
        ],
    )
    def test_tui(self, setup, select, keys):
        """Test the TUI access of the command."""

        def assertion(screen, logs, **kwargs):
            expected_screen = [
                "@misc{knuthwebsite,",
                "author = {Donald Knuth},",
                "title = {Knuth: Computers and Typesetting},",
                r"url = {http://www-cs-faculty.stanford.edu/\~{}uno/abcde.html}",
                "}",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            assert "knuthwebsite" in screen.display[0]

            expected_log = [
                ("cobib.commands.show", 10, "Show command triggered from TUI."),
                ("cobib.commands.show", 10, "Clearing current buffer contents."),
                ("cobib.commands.show", 10, "Starting Show command."),
                ("cobib.commands.show", 10, "Populating buffer with ShowCommand result."),
            ]
            if kwargs.get("select", False):
                expected_log.insert(
                    3,
                    (
                        "cobib.commands.show",
                        10,
                        "Current entry is selected. Applying highlighting.",
                    ),
                )
            assert [log for log in logs if log[0] == "cobib.commands.show"] == expected_log

            label_color = "magenta" if kwargs.get("select", False) else "cyan"
            assert [c.bg for c in screen.buffer[1].values()][0:6] == ["cyan"] * 6
            assert [c.bg for c in screen.buffer[1].values()][6:18] == [label_color] * 12
            assert [c.bg for c in screen.buffer[1].values()][18:] == ["cyan"] * 62

        self.run_tui(keys, assertion, {"select": select})
