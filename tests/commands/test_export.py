"""Tests for coBib's ExportCommand."""
# pylint: disable=no-self-use,unused-argument

import os
import tempfile
from zipfile import ZipFile

import pytest

from cobib.commands import ExportCommand
from cobib.database import Database

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

TMPDIR = tempfile.gettempdir()


class TestExportCommand(CommandTest, TUITest):
    """Tests for coBib's ExportCommand."""

    def get_command(self):
        """Get the command tested by this class."""
        return ExportCommand

    def _assert(self, args):
        """Common assertion utility method."""
        if "-b" in args:
            self._assert_bib(args)
        if "-z" in args:
            self._assert_zip(args)

    def _assert_bib(self, args):
        """Assertion utility method for bibtex output."""
        try:
            with open(os.path.join(TMPDIR, "cobib_test_export.bib"), "r") as file:
                with open(get_resource("example_literature.bib"), "r") as expected:
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
            os.remove(os.path.join(TMPDIR, "cobib_test_export.bib"))

    def _assert_zip(self, args):
        """Assertion utility method for bibtex output."""
        try:
            with ZipFile(os.path.join(TMPDIR, "cobib_test_export.zip"), "r") as file:
                # assert that the file does not contain a bad file
                assert file.testzip() is None
                assert file.namelist() == ["debug.py"]
                file.extract("debug.py", path=TMPDIR)
                with open(os.path.join(TMPDIR, "debug.py"), "r") as extracted:
                    with open(get_resource("debug.py"), "r") as truth:
                        assert extracted.read() == truth.read()
        finally:
            try:
                # clean up file system
                os.remove(os.path.join(TMPDIR, "cobib_test_export.zip"))
                os.remove(os.path.join(TMPDIR, "debug.py"))
            except FileNotFoundError:
                pass

    @pytest.mark.parametrize(
        ["args"],
        [
            [["-b", os.path.join(TMPDIR, "cobib_test_export.bib")]],
            [["-b", os.path.join(TMPDIR, "cobib_test_export.bib"), "--", "++ID", "einstein"]],
            [["-b", os.path.join(TMPDIR, "cobib_test_export.bib"), "-s", "--", "einstein"]],
            [["-z", os.path.join(TMPDIR, "cobib_test_export.zip")]],
            [["-z", os.path.join(TMPDIR, "cobib_test_export.zip"), "--", "++ID", "einstein"]],
            [["-z", os.path.join(TMPDIR, "cobib_test_export.zip"), "-s", "--", "einstein"]],
        ],
    )
    def test_command(self, setup, args):
        """Test the command itself."""
        if "-z" in args:
            # add a dummy file to the `einstein` entry
            entry = Database()["einstein"]
            entry.file = get_resource("debug.py")
        ExportCommand().execute(args)
        self._assert(args)

    def test_warning_missing_label(self, setup, caplog):
        """Test warning for missing label."""
        args = ["-b", os.path.join(TMPDIR, "cobib_test_export.bib"), "-s", "--", "dummy"]
        ExportCommand().execute(args)
        assert (
            "cobib.commands.export",
            30,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    def test_warning_missing_output(self, setup, caplog):
        """Test warning for missing output format."""
        args = ["-s", "--", "einstein"]
        ExportCommand().execute([args])
        assert ("cobib.commands.export", 40, "No output file specified!") in caplog.record_tuples

    @pytest.mark.parametrize(
        ["args"],
        [
            [["-b", os.path.join(TMPDIR, "cobib_test_export.bib")]],
        ],
    )
    # other variants are already covered by test_command
    def test_cmdline(self, setup, monkeypatch, args):
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, "main", ["cobib", "export"] + args)
        self._assert(args)

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "x-b" + os.path.join(TMPDIR, "cobib_test_export.bib") + " -- ++ID einstein\n"],
            [True, "Gvx-b" + os.path.join(TMPDIR, "cobib_test_export.bib") + "\n"],
        ],
    )
    def test_tui(self, setup, select, keys):
        """Test the TUI access of the command."""

        def assertion(screen, logs, **kwargs):
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
