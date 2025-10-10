"""Tests for coBib's ZipExporter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator
from zipfile import ZipFile

import pytest
from typing_extensions import override

from cobib.commands import ExportCommand
from cobib.config import Event, config
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

        TestZipExport._assert(include_files=True, include_notes=False)

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

    @pytest.fixture
    def post_setup(self) -> Generator[Any, None, None]:
        """Additional setup instructions."""
        # add a dummy file to the `einstein` entry
        entry = Database()["einstein"]
        entry.file = get_resource("debug.py")
        notes_file = self.COBIB_TEST_DIR / "einstein.txt"
        notes_file.touch()
        entry.notes = str(notes_file)

        yield

        notes_file.unlink(missing_ok=True)

    @staticmethod
    def _assert(*, include_files: bool, include_notes: bool) -> None:
        """Assertion utility method for zip output.

        Args:
            include_files: whether to assert included files.
            include_notes: whether to assert included notes.
        """
        try:
            with ZipFile(TMPDIR / "cobib_test_export.zip", "r") as file:
                # assert that the file does not contain a bad file
                assert file.testzip() is None
                namelist = []
                if include_files:
                    namelist.append("debug.py")
                if include_notes:
                    namelist.append("einstein.txt")
                assert file.namelist() == namelist
                if include_files:
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
    def test_command(self, setup: Any, post_setup: Any, args: list[str]) -> None:
        """Test exporting to zip via the ExportCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            args: the arguments to pass to the command.
        """
        ExportCommand(*args).execute()
        self._assert(include_files=True, include_notes=True)

    @pytest.mark.parametrize("config_overwrite", [True, False])
    @pytest.mark.parametrize("skip_files", [None, True, False])
    def test_skip_files(
        self, setup: Any, post_setup: Any, config_overwrite: bool, skip_files: bool | None
    ) -> None:
        """Test exporting to zip via the ExportCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            config_overwrite: what to overwrite `config.exporters.zip.skip_files` with.
            skip_files: the value for the `--skip-files` argument.
        """
        config.exporters.zip.skip_files = config_overwrite
        should_include_files = not config_overwrite
        args = ["--zip", "-s", "--", str(TMPDIR / "cobib_test_export.zip"), "--", "einstein"]
        if skip_files is True:
            should_include_files = False
            args.insert(3, "--skip-files")
        elif skip_files is False:
            should_include_files = True
            args.insert(3, "--include-files")

        ExportCommand(*args).execute()
        self._assert(include_files=should_include_files, include_notes=True)

    @pytest.mark.parametrize("config_overwrite", [True, False])
    @pytest.mark.parametrize("skip_notes", [None, True, False])
    def test_skip_notes(
        self, setup: Any, post_setup: Any, config_overwrite: bool, skip_notes: bool | None
    ) -> None:
        """Test exporting to zip via the ExportCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            config_overwrite: what to overwrite `config.exporters.zip.skip_notes` with.
            skip_notes: the value for the `--skip-notes` argument.
        """
        config.exporters.zip.skip_notes = config_overwrite
        should_include_notes = not config_overwrite
        args = ["--zip", "-s", "--", str(TMPDIR / "cobib_test_export.zip"), "--", "einstein"]
        if skip_notes is True:
            should_include_notes = False
            args.insert(3, "--skip-notes")
        elif skip_notes is False:
            should_include_notes = True
            args.insert(3, "--include-notes")

        ExportCommand(*args).execute()
        self._assert(include_notes=should_include_notes, include_files=True)
