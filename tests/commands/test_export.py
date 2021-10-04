"""Tests for coBib's ExportCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import os
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Type
from zipfile import ZipFile

import pytest

from cobib.commands import ExportCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

TMPDIR = Path(tempfile.gettempdir())

if TYPE_CHECKING:
    import cobib.commands


class TestExportCommand(CommandTest, TUITest):
    """Tests for coBib's ExportCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return ExportCommand

    def _assert(self, args: List[str]) -> None:
        """Common assertion utility method.

        Args:
            args: the arguments which were passed to the command.
        """
        if "-b" in args:
            self._assert_bib(args)
        if "-z" in args:
            self._assert_zip(args)

    def _assert_bib(self, args: List[str]) -> None:
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
                            file.__next__()
        finally:
            # clean up file system
            os.remove(TMPDIR / "cobib_test_export.bib")

    def _assert_zip(self, args: List[str]) -> None:
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
            try:
                # clean up file system
                os.remove(TMPDIR / "cobib_test_export.zip")
                os.remove(TMPDIR / "debug.py")
            except FileNotFoundError:
                pass

    @pytest.mark.parametrize(
        ["args"],
        [
            [["-b", str(TMPDIR / "cobib_test_export.bib")]],
            [["-b", str(TMPDIR / "cobib_test_export.bib"), "--", "++label", "einstein"]],
            [["-b", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "einstein"]],
            [["-z", str(TMPDIR / "cobib_test_export.zip")]],
            [["-z", str(TMPDIR / "cobib_test_export.zip"), "--", "++label", "einstein"]],
            [["-z", str(TMPDIR / "cobib_test_export.zip"), "-s", "--", "einstein"]],
        ],
    )
    def test_command(self, setup: Any, args: List[str]) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
        """
        if "-z" in args:
            # add a dummy file to the `einstein` entry
            entry = Database()["einstein"]
            entry.file = get_resource("debug.py")
        ExportCommand().execute(args)
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
        ExportCommand().execute(args)
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
            os.remove(TMPDIR / "cobib_test_export.bib")

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        args = ["-b", str(TMPDIR / "cobib_test_export.bib"), "-s", "--", "dummy"]
        ExportCommand().execute(args)
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
        ExportCommand().execute(args)
        assert ("cobib.commands.export", 40, "No output file specified!") in caplog.record_tuples

    @pytest.mark.parametrize(
        ["args"],
        [
            [["-b", str(TMPDIR / "cobib_test_export.bib")]],
        ],
    )
    # other variants are already covered by test_command
    def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch, args: List[str]) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            args: additional arguments to pass to the command.
        """
        self.run_module(monkeypatch, "main", ["cobib", "export"] + args)
        self._assert(args)

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "x-b" + str(TMPDIR / "cobib_test_export.bib") + " -- ++label einstein\n"],
            [True, "Gvx-b" + str(TMPDIR / "cobib_test_export.bib") + "\n"],
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
            dummy_args = ["-b"]
            if kwargs.get("selection", False):
                dummy_args += ["-s"]
            self._assert(dummy_args)

            expected_log = [
                ("cobib.commands.export", 10, "Export command triggered from TUI."),
                ("cobib.commands.export", 10, "Starting Export command."),
                ("cobib.commands.export", 20, 'Exporting entry "einstein".'),
            ]
            if kwargs.get("selection", False):
                expected_log.insert(
                    2,
                    (
                        "cobib.commands.export",
                        20,
                        "Selection given. Interpreting `filter` as a list of labels",
                    ),
                )
            else:
                expected_log.insert(
                    2,
                    (
                        "cobib.commands.export",
                        10,
                        "Gathering filtered list of entries to be exported.",
                    ),
                )

            assert [log for log in logs if log[0] == "cobib.commands.export"] == expected_log

        self.run_tui(keys, assertion, {"selection": select})

    def test_event_pre_export_command(self, setup: Any) -> None:
        """Tests the PreExportCommand event."""
        args = ["-b", str(TMPDIR / "cobib_test_export.bib")]

        @Event.PreExportCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.selection = True
            largs.filter = ["einstein"]

        assert Event.PreExportCommand.validate()

        ExportCommand().execute(args)

        self._assert_bib(["-s"] + args + ["--", "einstein"])

    def test_event_post_export_command(self, setup: Any) -> None:
        """Tests the PostExportCommand event."""
        args = ["-b", str(TMPDIR / "cobib_test_export.bib")]

        @Event.PostExportCommand.subscribe
        def hook(labels: List[str], largs: Namespace) -> None:
            os.remove(str(TMPDIR / "cobib_test_export.bib"))

        assert Event.PostExportCommand.validate()

        ExportCommand().execute(args)

        assert not os.path.exists(str(TMPDIR / "cobib_test_export.bib"))
