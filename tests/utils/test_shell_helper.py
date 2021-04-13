"""Tests for coBib's shell helper functions."""

from itertools import zip_longest

import pytest

from cobib.config import config
from cobib.utils import shell_helper

from .. import get_resource
from ..cmdline_test import CmdLineTest


class TestListCommands(CmdLineTest):
    """Tests for the shell helper to list commands."""

    EXPECTED = [
        "add",
        "delete",
        "edit",
        "export",
        "init",
        "list",
        "modify",
        "open",
        "redo",
        "search",
        "show",
        "undo",
    ]

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup():
        """Load testing config."""
        config.load(get_resource("debug.py"))

    # pylint: disable=no-self-use
    def test_method(self):
        """Test the shell_helper method itself."""
        cmds = shell_helper.list_commands()
        cmds = [c.split(":")[0] for c in cmds]
        assert cmds == TestListCommands.EXPECTED

    def test_cmdline(self, monkeypatch, capsys):
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_list_commands"])
        assert capsys.readouterr().out.split() == TestListCommands.EXPECTED

    def test_cmdline_via_main(self, monkeypatch, capsys):
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_list_commands"])
        assert capsys.readouterr().out.split() == TestListCommands.EXPECTED


class TestListLabels(CmdLineTest):
    """Tests for the shell helper to list labels."""

    EXPECTED = ["einstein", "latexcompanion", "knuthwebsite"]

    # pylint: disable=no-self-use
    def test_method(self):
        """Test the shell_helper method itself."""
        labels = shell_helper.list_labels()
        assert labels == TestListLabels.EXPECTED

    def test_cmdline(self, monkeypatch, capsys):
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_list_labels"])
        assert capsys.readouterr().out.split() == TestListLabels.EXPECTED

    def test_cmdline_via_main(self, monkeypatch, capsys):
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_list_labels"])
        assert capsys.readouterr().out.split() == TestListLabels.EXPECTED


class TestListFilters(CmdLineTest):
    """Tests for the shell helper to list filters."""

    EXPECTED = {
        "publisher",
        "ENTRYTYPE",
        "address",
        "ID",
        "journal",
        "doi",
        "year",
        "title",
        "author",
        "pages",
        "number",
        "volume",
        "url",
    }

    # pylint: disable=no-self-use
    def test_method(self):
        """Test the shell_helper method itself."""
        filters = shell_helper.list_filters()
        assert filters == TestListFilters.EXPECTED

    def test_cmdline(self, monkeypatch, capsys):
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_list_filters"])
        assert set(capsys.readouterr().out.split()) == TestListFilters.EXPECTED

    def test_cmdline_via_main(self, monkeypatch, capsys):
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_list_filters"])
        assert set(capsys.readouterr().out.split()) == TestListFilters.EXPECTED


class TestPrintExampleConfig(CmdLineTest):
    """Tests for the shell helper to print the example config."""

    # pylint: disable=no-self-use
    def test_method(self):
        """Test the shell_helper method itself."""
        example = shell_helper.example_config()
        with open(get_resource("example.py", "../src/cobib/config"), "r") as expected:
            for line, truth in zip_longest(example, expected):
                assert line == truth.strip()

    def _assert(self, output):
        """Common assertion utility method."""
        with open(get_resource("example.py", "../src/cobib/config"), "r") as expected:
            for line, truth in zip_longest(output, expected):
                try:
                    assert line == truth.strip()
                except AttributeError:
                    # an empty string can equal no string (i.e. None)
                    assert bool(line) == bool(truth)

    def test_cmdline(self, monkeypatch, capsys):
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_example_config"])
        self._assert(capsys.readouterr().out.split("\n"))

    def test_cmdline_via_main(self, monkeypatch, capsys):
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_example_config"])
        self._assert(capsys.readouterr().out.split("\n"))
