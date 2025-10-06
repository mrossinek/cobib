"""Tests for coBib's ExportCommand."""

from __future__ import annotations

import tempfile
from argparse import ArgumentError
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ExportCommand
from cobib.config import Event

from .command_test import CommandTest

TMPDIR = Path(tempfile.gettempdir())

if TYPE_CHECKING:
    import cobib.commands


class TestExportCommand(CommandTest):
    """Tests for coBib's ExportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ExportCommand

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        args = ["--bibtex", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "dummy"]
        ExportCommand(*args).execute()
        try:
            assert (
                "cobib.commands.export",
                30,
                "No entry with the label 'dummy' could be found.",
            ) in caplog.record_tuples
        finally:
            # clean up file system
            (TMPDIR / "cobib_test_export.bib").unlink(missing_ok=True)

    def test_warning_missing_output(self, setup: Any) -> None:
        """Test warning for missing output format.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        args = ["-s", "--", "einstein"]
        with pytest.raises(SystemExit):
            ExportCommand(*args)

    def test_warning_separators(self, setup: Any) -> None:
        """Test warning for too many separators.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        args = ["-s", "--bibtex", "--", "--", "tmp.bib", "--", "einstein"]
        with pytest.raises(ArgumentError):
            ExportCommand(*args)

    @pytest.mark.asyncio
    async def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            await self.run_module(monkeypatch, "main", ["cobib", "export", "-h"])

    def test_event_pre_export_command(self, setup: Any) -> None:
        """Tests the PreExportCommand event."""
        args = ["--bibtex", str(TMPDIR / "cobib_test_export.bib")]

        @Event.PreExportCommand.subscribe
        def hook(command: ExportCommand) -> None:
            (TMPDIR / "cobib_test_export.bib").unlink()

        assert Event.PreExportCommand.validate()

        with pytest.raises(FileNotFoundError):
            ExportCommand(*args).execute()

    def test_event_post_export_command(self, setup: Any) -> None:
        """Tests the PostExportCommand event."""
        args = ["--bibtex", str(TMPDIR / "cobib_test_export.bib")]

        @Event.PostExportCommand.subscribe
        def hook(command: ExportCommand) -> None:
            (TMPDIR / "cobib_test_export.bib").unlink()

        assert Event.PostExportCommand.validate()

        ExportCommand(*args).execute()

        assert not (TMPDIR / "cobib_test_export.bib").exists()
