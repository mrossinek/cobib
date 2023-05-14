"""Tests for coBib's ImportCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type

import pytest
from typing_extensions import override

from cobib.commands import ImportCommand
from cobib.config import Event

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestImportCommand(CommandTest):
    """Tests for coBib's ImportCommand."""

    @override
    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        return ImportCommand

    def test_command(self) -> None:
        """Test the command itself."""
        with pytest.raises(SystemExit):
            ImportCommand("-h").execute()

    @pytest.mark.asyncio
    async def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            await self.run_module(monkeypatch, "main", ["cobib", "import", "-h"])

    def test_event_pre_import_command(self, setup: Any) -> None:
        """Tests the PreImportCommand event."""

        @Event.PreImportCommand.subscribe
        def hook(command: ImportCommand) -> None:
            command.largs.zotero = False

        assert Event.PreImportCommand.validate()

        ImportCommand("--zotero").execute()

    def test_event_post_import_command(self, setup: Any) -> None:
        """Tests the PostImportCommand event."""

        @Event.PostImportCommand.subscribe
        def hook(command: ImportCommand) -> None:
            pass

        assert Event.PostImportCommand.validate()

        @Event.PreImportCommand.subscribe
        def aux_hook(command: ImportCommand) -> None:
            command.largs.zotero = False

        ImportCommand("--zotero").execute()
