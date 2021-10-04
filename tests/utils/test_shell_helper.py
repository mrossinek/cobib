"""Tests for coBib's shell helper functions."""

import logging
import os
import subprocess
import tempfile
from itertools import zip_longest
from pathlib import Path
from shutil import copyfile, rmtree
from typing import Generator, List, Optional, Set, Union

import pytest

from cobib.config import config
from cobib.database import Database
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


class ShellHelperTest(CmdLineTest):
    """A base class for some common shell helper unit tests."""

    COMMAND: Optional[str] = None
    """The name of the shell helper command-"""

    EXPECTED: Optional[Union[str, List[str], Set[str]]] = None
    """The expected outcome."""

    def _assert(self, out: str) -> None:
        """The utility assertion method.

        Args:
            out: The captured output of the shell helper function.
        """
        if isinstance(self.EXPECTED, list):
            assert out.split() == self.EXPECTED
        elif isinstance(self.EXPECTED, set):
            assert set(out.split()) == self.EXPECTED

    def test_method(self) -> None:
        """Test the shell_helper method itself."""
        args: List[str] = []
        cmds = getattr(shell_helper, str(self.COMMAND))(args)
        self._assert("\n".join(cmds))

    def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method.

        Args:
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        CmdLineTest.run_module(monkeypatch, "helper_main", ["cobib", f"_{self.COMMAND}"])
        self._assert(capsys.readouterr().out)

    def test_cmdline_via_main(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the helper method via the main method.

        Args:
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            CmdLineTest.run_module(monkeypatch, "main", ["cobib", f"_{self.COMMAND}"])
        self._assert(capsys.readouterr().out)


class TestListCommands(ShellHelperTest):
    """Tests for the shell helper which lists the available commands."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> None:
        """Setup debugging config.

        This fixture is automatically enabled for all tests in this class.
        """
        config.defaults()
        config.load(get_resource("debug.py"))

    COMMAND = "list_commands"
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


class TestListLabels(ShellHelperTest):
    """Tests for the shell helper which lists the existing labels."""

    COMMAND = "list_labels"
    EXPECTED = ["einstein", "latexcompanion", "knuthwebsite"]


class TestListFilters(ShellHelperTest):
    """Tests for the shell helper which lists the existing filters."""

    COMMAND = "list_filters"
    EXPECTED = {
        "publisher",
        "ENTRYTYPE",
        "address",
        "label",
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


class TestPrintExampleConfig(ShellHelperTest):
    """Tests for the shell helper which prints the example configuration."""

    COMMAND = "example_config"
    EXPECTED = get_resource("example.py", "../src/cobib/config")

    def _assert(self, out: str) -> None:
        with open(self.EXPECTED, "r", encoding="utf-8") as expected:
            for line, truth in zip_longest(out.split("\n"), expected):
                try:
                    assert line == truth.strip()
                except AttributeError:
                    # an empty string can equal no string (i.e. None)
                    assert bool(line) == bool(truth)


class TestLintDatabase(ShellHelperTest):
    """Tests for the shell helper which lints the users database."""

    COMMAND = "lint_database"
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
        """Set linting database path.

        This fixture is automatically enabled for all tests in this class.
        """
        config.defaults()
        config.database.file = str(TestLintDatabase.REL_PATH)

    def _assert(self, out: str) -> None:
        for msg, truth in zip_longest(out.split("\n"), self.EXPECTED):
            if msg.strip() and truth:
                assert msg == truth

    # pylint: disable=no-self-use
    def test_no_lint_warnings(self) -> None:
        """Test the case of no raised lint warnings."""
        config.load(get_resource("debug.py"))
        args: List[str] = []
        lint_messages = shell_helper.lint_database(args)
        for msg, exp in zip_longest(
            lint_messages, ["Congratulations! Your database triggers no lint messages."]
        ):
            if msg.strip() and exp:
                assert msg == exp

    @pytest.mark.parametrize("git", [False, True])
    def test_lint_auto_format(self, git: bool) -> None:
        """Test automatic lint formatter.

        Args:
            git: whether or not git-tracking should be enabled.
        """
        tmp_dir = Path(tempfile.gettempdir()).resolve()
        cobib_test_dir = tmp_dir / "cobib_lint_test"
        cobib_test_dir.mkdir(parents=True, exist_ok=True)
        cobib_test_dir_git = cobib_test_dir / ".git"

        database_file = RelPath(cobib_test_dir / "database.yaml")

        copyfile(TestLintDatabase.REL_PATH.path, database_file.path)
        config.database.file = str(database_file)
        config.database.git = git

        if git:
            commands = [
                f"cd {cobib_test_dir}",
                "git init",
                "git add -- database.yaml",
                "git commit --no-gpg-sign --quiet --message 'Initial commit'",
            ]
            os.system("; ".join(commands))

        try:
            # apply linting with formatting and check for the expected lint messages
            args: List[str] = ["--format"]
            pre_lint_messages = shell_helper.lint_database(args)
            expected_messages = [
                "The following lint messages have successfully been resolved:"
            ] + self.EXPECTED
            for msg, truth in zip_longest(pre_lint_messages, expected_messages):
                if msg.strip() and truth:
                    assert msg == truth.replace(str(TestLintDatabase.REL_PATH), str(database_file))

            # assert auto-formatted database
            with open(database_file.path, "r", encoding="utf-8") as file:
                with open(
                    get_resource("fixed_database.yaml", "utils"), "r", encoding="utf-8"
                ) as expected:
                    for line, truth in zip_longest(file.readlines(), expected.readlines()):
                        assert line == truth

            # assert git message
            if git:
                with subprocess.Popen(
                    [
                        "git",
                        "-C",
                        cobib_test_dir_git,
                        "show",
                        "--format=format:%B",
                        "--no-patch",
                        "HEAD",
                    ],
                    stdout=subprocess.PIPE,
                ) as proc:
                    message, _ = proc.communicate()
                    # decode it
                    split_msg = message.decode("utf-8").split("\n")
                    if split_msg is None:
                        return
                    # assert subject line
                    assert "Auto-commit: LintCommand" in split_msg[0]

            # recheck linting and assert no lint messages
            post_lint_messages = shell_helper.lint_database([])
            for msg, exp in zip_longest(
                post_lint_messages, ["Congratulations! Your database triggers no lint messages."]
            ):
                if msg.strip() and exp:
                    assert msg == exp

        finally:
            rmtree(cobib_test_dir)
            Database().clear()


class TestUnifyLabels(ShellHelperTest):
    """Tests for the shell helper which unifies all database labels."""

    COMMAND = "unify_labels"
    REL_PATH = RelPath(get_resource("unifying_database.yaml", "utils"))
    EXPECTED: List[str] = [
        "[INFO] einstein: changing field 'label' from einstein to Einstein1905_a",
        "[INFO] latexcompanion: changing field 'label' from latexcompanion to Goossens1993",
        "[INFO] knuthwebsite: changing field 'label' from knuthwebsite to Knuth",
        "[INFO] Einstein_1905: changing field 'label' from Einstein_1905 to Einstein1905_b",
        "[INFO] Einstein1905: changing field 'label' from Einstein1905 to Einstein1905_c",
        "[INFO] einstein_2: changing field 'label' from einstein_2 to Einstein1905_d",
    ]

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> None:
        """Set linting database path.

        This fixture is automatically enabled for all tests in this class.
        """
        config.defaults()
        config.database.format.label_default = "{author.split()[1]}{year}"
        config.database.file = str(TestUnifyLabels.REL_PATH)

    def _assert(self, out: str) -> None:
        filtered = [line for line in out.split("\n") if line.startswith("[INFO]")]
        for msg, truth in zip_longest(filtered, self.EXPECTED):
            if msg.strip() and truth:
                assert msg == truth

    @pytest.mark.parametrize("git", [False, True])
    def test_unify_labels(self, git: bool) -> None:
        # pylint: disable=no-self-use
        """Test actual changes of label unification.

        Args:
            git: whether or not git-tracking should be enabled.
        """
        tmp_dir = Path(tempfile.gettempdir()).resolve()
        cobib_test_dir = tmp_dir / "cobib_unify_label_test"
        cobib_test_dir.mkdir(parents=True, exist_ok=True)
        cobib_test_dir_git = cobib_test_dir / ".git"

        database_file = RelPath(cobib_test_dir / "database.yaml")

        copyfile(TestUnifyLabels.REL_PATH.path, database_file.path)
        config.database.file = str(database_file)
        config.database.git = git

        if git:
            commands = [
                f"cd {cobib_test_dir}",
                "git init",
                "git add -- database.yaml",
                "git commit --no-gpg-sign --quiet --message 'Initial commit'",
            ]
            os.system("; ".join(commands))

        try:
            # apply label unification
            shell_helper.unify_labels(["--apply"])

            # assert unified database
            with open(database_file.path, "r", encoding="utf-8") as file:
                with open(
                    RelPath(get_resource("unified_database.yaml", "utils")).path,
                    "r",
                    encoding="utf-8",
                ) as expected:
                    for line, truth in zip_longest(file.readlines(), expected.readlines()):
                        assert line == truth

            # assert git message
            if git:
                with subprocess.Popen(
                    [
                        "git",
                        "-C",
                        cobib_test_dir_git,
                        "show",
                        "--format=format:%B",
                        "--no-patch",
                        "HEAD",
                    ],
                    stdout=subprocess.PIPE,
                ) as proc:
                    message, _ = proc.communicate()
                    # decode it
                    split_msg = message.decode("utf-8").split("\n")
                    if split_msg is None:
                        return
                    # assert subject line
                    assert "Auto-commit: ModifyCommand" in split_msg[0]

        finally:
            rmtree(cobib_test_dir)
            Database().clear()
