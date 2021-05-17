"""Tests for coBib's shell helper functions."""

import logging
from itertools import zip_longest
from typing import Generator, List

import pytest

from cobib.config import config
from cobib.utils import shell_helper
from cobib.utils.rel_path import RelPath

from .. import get_resource
from ..cmdline_test import CmdLineTest

LOGGER = logging.getLogger()


@pytest.fixture(autouse=True)
def ensure_logging_not_altered() -> Generator[None, None, None]:
    """Ensures that the logging framework remains unaltered.

    Reference:
        https://github.com/pytest-dev/pytest/issues/5743
    """
    before_handlers = list(LOGGER.handlers)
    yield
    LOGGER.handlers = before_handlers


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
    def setup() -> None:
        """Load testing config."""
        config.load(get_resource("debug.py"))

    # pylint: disable=no-self-use
    def test_method(self) -> None:
        """Test the shell_helper method itself."""
        cmds = shell_helper.list_commands()
        cmds = [c.split(":")[0] for c in cmds]
        assert cmds == TestListCommands.EXPECTED

    def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_list_commands"])
        assert capsys.readouterr().out.split() == TestListCommands.EXPECTED

    def test_cmdline_via_main(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_list_commands"])
        assert capsys.readouterr().out.split() == TestListCommands.EXPECTED


class TestListLabels(CmdLineTest):
    """Tests for the shell helper to list labels."""

    EXPECTED = ["einstein", "latexcompanion", "knuthwebsite"]

    # pylint: disable=no-self-use
    def test_method(self) -> None:
        """Test the shell_helper method itself."""
        labels = shell_helper.list_labels()
        assert labels == TestListLabels.EXPECTED

    def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_list_labels"])
        assert capsys.readouterr().out.split() == TestListLabels.EXPECTED

    def test_cmdline_via_main(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
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
    def test_method(self) -> None:
        """Test the shell_helper method itself."""
        filters = shell_helper.list_filters()
        assert filters == TestListFilters.EXPECTED

    def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_list_filters"])
        assert set(capsys.readouterr().out.split()) == TestListFilters.EXPECTED

    def test_cmdline_via_main(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_list_filters"])
        assert set(capsys.readouterr().out.split()) == TestListFilters.EXPECTED


class TestPrintExampleConfig(CmdLineTest):
    """Tests for the shell helper to print the example config."""

    # pylint: disable=no-self-use
    def test_method(self) -> None:
        """Test the shell_helper method itself."""
        example = shell_helper.example_config()
        with open(get_resource("example.py", "../src/cobib/config"), "r") as expected:
            for line, truth in zip_longest(example, expected):
                assert line == truth.strip()

    def _assert(self, output: List[str]) -> None:
        """Common assertion utility method."""
        with open(get_resource("example.py", "../src/cobib/config"), "r") as expected:
            for line, truth in zip_longest(output, expected):
                try:
                    assert line == truth.strip()
                except AttributeError:
                    # an empty string can equal no string (i.e. None)
                    assert bool(line) == bool(truth)

    def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_example_config"])
        self._assert(capsys.readouterr().out.split("\n"))

    def test_cmdline_via_main(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_example_config"])
        self._assert(capsys.readouterr().out.split("\n"))


class TestLintDatabase(CmdLineTest):
    """Tests for the shell helper to lint the database."""

    REL_PATH = RelPath(get_resource("linting_database.yaml", "utils"))
    EXPECTED = [
        f"{REL_PATH}:5 Converted the field 'file' of entry 'dummy' to a list. You can consider "
        "storing it as such directly.",
        f"{REL_PATH}:6 Converting field 'month' of entry 'dummy' from '8' to 'aug'.",
        f"{REL_PATH}:7 Converting field 'number' of entry 'dummy' to integer: 1.",
        f"{REL_PATH}:8 Converted the field 'tags' of entry 'dummy' to a list. You can consider "
        "storing it as such directly.",
        f"{REL_PATH}:9 Converted the field 'url' of entry 'dummy' to a list. You can consider "
        "storing it as such directly.",
        f"{REL_PATH}:4 The field 'ID' of entry 'dummy' is no longer required. It will be inferred "
        "from the entry label.",
    ]

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> None:
        """Load testing config."""
        config.database.file = str(TestLintDatabase.REL_PATH)

    # pylint: disable=no-self-use
    def test_no_lint_warnings(self) -> None:
        """Test the case of no raised lint warnings."""
        config.load(get_resource("debug.py"))
        lint_messages = shell_helper.lint_database()
        for msg, exp in zip_longest(
            lint_messages, ["Congratulations! Your database triggers no lint messages."]
        ):
            if msg.strip() and exp:
                assert msg == exp

    # pylint: disable=no-self-use
    def test_method(self) -> None:
        """Test the shell_helper method itself."""
        lint_messages = shell_helper.lint_database()
        for msg, exp in zip_longest(lint_messages, TestLintDatabase.EXPECTED):
            if msg.strip() and exp:
                assert msg == exp

    def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method."""
        self.run_module(monkeypatch, "helper_main", ["cobib", "_lint_database"])
        for msg, exp in zip_longest(capsys.readouterr().out.split("\n"), TestLintDatabase.EXPECTED):
            if msg.strip() and exp:
                assert msg == exp

    def test_cmdline_via_main(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method via the main method."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "_lint_database"])
        for msg, exp in zip_longest(capsys.readouterr().out.split("\n"), TestLintDatabase.EXPECTED):
            if msg.strip() and exp:
                assert msg == exp
