"""Tests for coBib's BibtexExporter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ExportCommand
from cobib.config import Event, config
from cobib.database import Database
from cobib.exporters import BibtexExporter

from .. import get_resource
from ..commands import CommandTest
from .exporter_test import ExporterTest

if TYPE_CHECKING:
    import cobib.commands

TMPDIR = Path(tempfile.gettempdir())


class TestBibtexExporter(ExporterTest):
    """Tests for coBib's BibtexExporter."""

    def test_event_pre_bibtex_export(self) -> None:
        """Tests the PreBibtexExport event."""

        @Event.PreBibtexExport.subscribe
        def hook(exporter: BibtexExporter) -> None:
            exporter.exported_entries = [Database()["einstein"]]

        assert Event.PreBibtexExport.validate()

        path = str(TMPDIR / "cobib_test_export.bib")
        BibtexExporter(path).write([])

        TestBibtexExport._assert(["-s", "--bibtex", path, "--", "einstein"])

    def test_event_post_bibtex_export(self) -> None:
        """Tests the PostBibtexExport event."""
        path = TMPDIR / "cobib_test_export.bib"

        @Event.PostBibtexExport.subscribe
        def hook(exporter: BibtexExporter) -> None:
            exporter.largs.file.write("test")

        assert Event.PostBibtexExport.validate()

        BibtexExporter(str(path)).write([Database()["einstein"]])

        try:
            assert open(path, "r", encoding="utf-8").readlines()[-1] == "test"
        finally:
            path.unlink(missing_ok=True)


class TestBibtexExport(CommandTest):
    """Tests for coBib's BibtexExporter via the ExportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ExportCommand

    @staticmethod
    def _assert(args: list[str]) -> None:
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
            (TMPDIR / "cobib_test_export.bib").unlink(missing_ok=True)

    @pytest.mark.parametrize(
        ["args"],
        [
            [["--bibtex", "--", str(TMPDIR / "cobib_test_export.bib")]],
            [
                [
                    "--bibtex",
                    "--",
                    str(TMPDIR / "cobib_test_export.bib"),
                    "--",
                    "++label",
                    "einstein",
                ]
            ],
            [["--bibtex", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "einstein"]],
            # the following limit test works only if "einstein" is the first entry in the database
            [["--bibtex", str(TMPDIR / "cobib_test_export.bib"), "--", "-l", "1"]],
        ],
    )
    def test_command(self, setup: Any, args: list[str]) -> None:
        """Test exporting to bibtex via the ExportCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
        """
        if "--zip" in args:
            # add a dummy file to the `einstein` entry
            entry = Database()["einstein"]
            entry.file = get_resource("debug.py")

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
        args = [
            "-s",
            "--bibtex",
            "--",
            str(TMPDIR / "cobib_test_export.bib"),
            "-a",
            "--",
            "einstein",
        ]
        if dotless:
            args.insert(5, "--dotless")
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
                    break
                else:
                    assert False
        finally:
            # clean up file system
            (TMPDIR / "cobib_test_export.bib").unlink(missing_ok=True)
