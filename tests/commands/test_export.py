"""Tests for coBib's ExportCommand."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import pytest
from typing_extensions import override

from cobib.commands import ExportCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import get_resource
from .command_test import CommandTest

TMPDIR = Path(tempfile.gettempdir())

if TYPE_CHECKING:
    import cobib.commands


class TestExportCommand(CommandTest):
    """Tests for coBib's ExportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ExportCommand

    def _assert(self, args: list[str]) -> None:
        """Common assertion utility method.

        Args:
            args: the arguments which were passed to the command.
        """
        if "-b" in args:
            self._assert_bib(args)
        if "-z" in args:
            self._assert_zip(args)

    def _assert_bib(self, args: list[str]) -> None:
        """Assertion utility method for bibtex output.

        Args:
            args: the arguments which were passed to the command.
        """
        try:
            with open(TMPDIR / "cobib_test_export.bib", "r", encoding="utf-8") as file:
                with open(
                    get_resource("example_literature.bib"), "r", encoding="utf-8"
                ) as expected:
                    # NOTE: do NOT use zip_longest to omit later entries
                    for line, truth in zip(file, expected):
                        if truth[0] == "%":
                            # ignore comments
                            continue
                        assert line == truth
                    if "-s" in args:
                        with pytest.raises(StopIteration):
                            next(file)
        finally:
            # clean up file system
            (TMPDIR / "cobib_test_export.bib").unlink()

    def _assert_zip(self, args: list[str]) -> None:
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
            [["-b", str(TMPDIR / "cobib_test_export.bib")]],
            [["-b", str(TMPDIR / "cobib_test_export.bib"), "--", "++label", "einstein"]],
            [["-b", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "einstein"]],
            # the following limit test works only if "einstein" is the first entry in the database
            [["-b", str(TMPDIR / "cobib_test_export.bib"), "--", "-l", "1"]],
            [["-z", str(TMPDIR / "cobib_test_export.zip")]],
            [["-z", str(TMPDIR / "cobib_test_export.zip"), "--", "++label", "einstein"]],
            [["-z", str(TMPDIR / "cobib_test_export.zip"), "-s", "--", "einstein"]],
            # the following limit test works only if "einstein" is the first entry in the database
            [["-z", str(TMPDIR / "cobib_test_export.zip"), "--", "-l", "1"]],
        ],
    )
    def test_command(self, setup: Any, args: list[str]) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
        """
        if "-z" in args:
            # add a dummy file to the `einstein` entry
            entry = Database()["einstein"]
            entry.file = get_resource("debug.py")  # type: ignore[assignment]
        ExportCommand(*args).execute()
        self._assert(args)

    @pytest.mark.parametrize("dotless", [False, True])
    def test_journal_abbreviation(self, setup: Any, dotless: bool) -> None:
        """Test journal abbreviation.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            dotless: whether to abbreviate with or without punctuation.
        """
        config.utils.journal_abbreviations = [("Annalen der Physik", "Ann. Phys.")]
        args = ["-a", "-b", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "einstein"]
        if dotless:
            args.insert(1, "--dotless")
        ExportCommand(*args).execute()
        self._assert_journal_abbreviation(dotless)

    def _assert_journal_abbreviation(self, dotless: bool) -> None:
        """Assertion utility method for bibtex output.

        Args:
            dotless: whether to abbreviate with or without punctuation.
        """
        try:
            with open(TMPDIR / "cobib_test_export.bib", "r", encoding="utf-8") as file:
                for line in file:
                    if "journal" not in line:
                        continue
                    expected = "Ann Phys" if dotless else "Ann. Phys."
                    assert expected in line
        finally:
            # clean up file system
            (TMPDIR / "cobib_test_export.bib").unlink()

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        args = ["-b", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "dummy"]
        ExportCommand(*args).execute()
        assert (
            "cobib.commands.export",
            30,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    def test_warning_missing_output(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing output format.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        args = ["-s", "--", "einstein"]
        ExportCommand(*args).execute()
        assert ("cobib.commands.export", 40, "No output file specified!") in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args"],
        [
            [["-b", str(TMPDIR / "cobib_test_export.bib")]],
        ],
    )
    # other variants are already covered by test_command
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, args: list[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            args: additional arguments to pass to the command.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "export", *args])
        self._assert(args)

    def test_event_pre_export_command(self, setup: Any) -> None:
        """Tests the PreExportCommand event."""
        args = ["-b", str(TMPDIR / "cobib_test_export.bib")]

        @Event.PreExportCommand.subscribe
        def hook(command: ExportCommand) -> None:
            command.largs.selection = True
            command.largs.filter = ["einstein"]

        assert Event.PreExportCommand.validate()

        ExportCommand(*args).execute()

        self._assert_bib(["-s", *args, "--", "einstein"])

    def test_event_post_export_command(self, setup: Any) -> None:
        """Tests the PostExportCommand event."""
        args = ["-b", str(TMPDIR / "cobib_test_export.bib")]

        @Event.PostExportCommand.subscribe
        def hook(command: ExportCommand) -> None:
            (TMPDIR / "cobib_test_export.bib").unlink()

        assert Event.PostExportCommand.validate()

        ExportCommand(*args).execute()

        assert not (TMPDIR / "cobib_test_export.bib").exists()
