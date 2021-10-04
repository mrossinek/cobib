"""Tests for coBib's ShowCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

from argparse import Namespace
from io import StringIO
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, List, Optional, Type

import pytest

from cobib.commands import ShowCommand
from cobib.config import Event

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestShowCommand(CommandTest, TUITest):
    """Tests for coBib's ShowCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return ShowCommand

    def _assert(self, output: List[str]) -> None:
        """Common assertion utility method.

        Args:
            output: the actual output of the command.
        """
        with open(get_resource("example_literature.bib"), "r", encoding="utf-8") as expected:
            # we use zip_longest to ensure that we don't have more than we expect
            for line, truth in zip_longest(output, expected):
                if not line:
                    continue
                assert line == truth.strip("\n")

    def test_command(self, setup: Any) -> None:  # type: ignore
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        # redirect output of show to string
        file = StringIO()
        ShowCommand().execute(["einstein"], out=file)
        self._assert(file.getvalue().split("\n"))

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        ShowCommand().execute(["dummy"])
        assert (
            "cobib.commands.show",
            40,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        self.run_module(monkeypatch, "main", ["cobib", "show", "einstein"])
        self._assert(capsys.readouterr().out.strip().split("\n"))

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "\n"],
            [True, "v\n"],
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

    def test_event_pre_show_command(self, setup: Any) -> None:
        """Tests the PreShowCommand event."""

        @Event.PreShowCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.label = "einstein"

        assert Event.PreShowCommand.validate()

        file = StringIO()
        ShowCommand().execute(["knuthwebsite"], out=file)
        self._assert(file.getvalue().split("\n"))

    def test_event_post_show_command(self, setup: Any) -> None:
        """Tests the PostShowCommand event."""

        @Event.PostShowCommand.subscribe
        def hook(entry_str: str) -> Optional[str]:
            return "Hello world!"

        assert Event.PostShowCommand.validate()

        file = StringIO()
        ShowCommand().execute(["knuthwebsite"], out=file)
        assert file.getvalue() == "Hello world!\n"
