"""Tests for coBib's ZipExporter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import pytest
from typing_extensions import override

from cobib.commands import ExportCommand
from cobib.config import Event
from cobib.database import Database
from cobib.exporters import ZipExporter

from .. import get_resource
from ..commands import CommandTest
from .exporter_test import ExporterTest

if TYPE_CHECKING:
    import cobib.commands

TMPDIR = Path(tempfile.gettempdir())


class TestZipExporter(ExporterTest):
    """Tests for coBib's ZipExporter."""

    def test_event_pre_zip_export(self) -> None:
        """Tests the PreZipExport event."""
        # add a dummy file to the `einstein` entry
        entry = Database()["einstein"]
        entry.file = get_resource("debug.py")

        @Event.PreZipExport.subscribe
        def hook(exporter: ZipExporter) -> None:
            exporter.exported_entries = [Database()["einstein"]]

        assert Event.PreZipExport.validate()

        args = [str(TMPDIR / "cobib_test_export.zip")]
        ZipExporter(*args).write([])

        TestZipExport._assert(["--zip", *args])

    def test_event_post_zip_export(self) -> None:
        """Tests the PostZipExport event."""
        # add a dummy file to the `einstein` entry
        entry = Database()["einstein"]
        entry.file = get_resource("debug.py")

        @Event.PostZipExport.subscribe
        def hook(exporter: ZipExporter) -> None:
            exporter.largs.file.comment = b"test"

        assert Event.PostZipExport.validate()

        path = TMPDIR / "cobib_test_export.zip"
        ZipExporter(str(path)).write([Database()["einstein"]])

        try:
            assert ZipFile(path, "r").comment == b"test"
        finally:
            path.unlink(missing_ok=True)


class TestZipExport(CommandTest):
    """Tests for coBib's ZipExporter via the ExportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ExportCommand

    @staticmethod
    def _assert(args: list[str]) -> None:
        """Assertion utility method for zip output.

        Args:
            args: the arguments which were passed to the command.
        """
        try:
            with ZipFile(TMPDIR / "cobib_test_export.zip", "r") as file:
                # assert that the file does not contain a bad file
                assert file.testzip() is None
                assert file.namelist() == ["debug.py"]
                file.extract("debug.py", path=TMPDIR)
                with open(TMPDIR / "debug.py", "r", encoding="utf-8") as extracted:
                    with open(get_resource("debug.py"), "r", encoding="utf-8") as truth:
                        assert extracted.read() == truth.read()
        finally:
            # clean up file system
            (TMPDIR / "cobib_test_export.zip").unlink(missing_ok=True)
            (TMPDIR / "debug.py").unlink(missing_ok=True)

    @pytest.mark.parametrize(
        ["args"],
        [
            [["--zip", str(TMPDIR / "cobib_test_export.zip")]],
            [["--zip", str(TMPDIR / "cobib_test_export.zip"), "--", "++label", "einstein"]],
            [["--zip", str(TMPDIR / "cobib_test_export.zip"), "-s", "--", "einstein"]],
            # the following limit test works only if "einstein" is the first entry in the database
            [["--zip", str(TMPDIR / "cobib_test_export.zip"), "--", "-l", "1"]],
        ],
    )
    def test_command(self, setup: Any, args: list[str]) -> None:
        """Test exporting to zip via the ExportCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
        """
        # add a dummy file to the `einstein` entry
        entry = Database()["einstein"]
        entry.file = get_resource("debug.py")

        ExportCommand(*args).execute()
        self._assert(args)
