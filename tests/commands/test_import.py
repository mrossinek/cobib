"""Tests for coBib's ImportCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import logging
from argparse import Namespace
from typing import TYPE_CHECKING, Any, Dict, Type

import pytest

from cobib.commands import ImportCommand
from cobib.config import Event
from cobib.database import Entry

from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestImportCommand(CommandTest, TUITest):
    """Tests for coBib's ImportCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return ImportCommand

    def get_safe_command_name(self) -> str:
        # noqa: D102
        return "import_"

    def test_command(self) -> None:
        """Test the command itself."""
        with pytest.raises(SystemExit):
            ImportCommand().execute(["-h"])

    def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "import", "-h"])

    def test_tui(self, setup: Any) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            for source, level, message in logs:
                if ("cobib.tui.tui", logging.INFO) == (
                    source,
                    level,
                ) and "sys.stderr contains:usage: import [-h] [--skip-download]" in message:
                    break
            else:
                pytest.fail("No help message logged to sys.stderr.")

        keys = "i\n"
        self.run_tui(keys, assertion, {})

    def test_event_pre_import_command(self, setup: Any) -> None:
        """Tests the PreImportCommand event."""

        @Event.PreImportCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.zotero = False

        assert Event.PreImportCommand.validate()

        ImportCommand().execute(["--zotero"])

    def test_event_post_import_command(self, setup: Any) -> None:
        """Tests the PostImportCommand event."""

        @Event.PostImportCommand.subscribe
        def hook(new_entries: Dict[str, Entry]) -> None:
            pass

        assert Event.PostImportCommand.validate()

        @Event.PreImportCommand.subscribe
        def aux_hook(largs: Namespace) -> None:
            largs.zotero = False

        ImportCommand().execute(["--zotero"])
