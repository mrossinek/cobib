"""Tests for coBib's ImportCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ImportCommand
from cobib.config import Event

from .. import get_resource
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestImportCommand(CommandTest):
    """Tests for coBib's ImportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ImportCommand

    @pytest.mark.asyncio
    async def test_command(self) -> None:  # type: ignore[override]
        """Test the command itself."""
        with pytest.raises(SystemExit):
            await ImportCommand("-h").execute()

    @pytest.mark.asyncio
    async def test_handle_identical(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of an identical entry being added.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            capsys: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
        """
        cmd = ImportCommand("--bibtex", get_resource("example_literature.bib"))
        await cmd.execute()

        assert len(cmd.new_entries) == 0

        assert (
            "cobib.database.database",
            35,
            (
                "Even though the label 'einstein' already exists in the runtime database, the "
                "entry is identical and, thus, no further disambiguation is necessary."
            ),
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    async def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            await self.run_module(monkeypatch, "main", ["cobib", "import", "-h"])

    @pytest.mark.asyncio
    async def test_event_pre_import_command(self, setup: Any) -> None:
        """Tests the PreImportCommand event."""

        @Event.PreImportCommand.subscribe
        def hook(command: ImportCommand) -> None:
            command.largs.bibtex = False

        assert Event.PreImportCommand.validate()

        await ImportCommand("--bibtex").execute()

    @pytest.mark.asyncio
    async def test_event_post_import_command(self, setup: Any) -> None:
        """Tests the PostImportCommand event."""

        @Event.PostImportCommand.subscribe
        def hook(command: ImportCommand) -> None:
            pass

        assert Event.PostImportCommand.validate()

        @Event.PreImportCommand.subscribe
        def aux_hook(command: ImportCommand) -> None:
            command.largs.bibtex = False

        await ImportCommand("--bibtex").execute()
