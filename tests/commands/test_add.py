"""Tests for coBib's AddCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import os
import tempfile
from argparse import Namespace
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

import pytest

from cobib.commands import AddCommand
from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.utils.rel_path import RelPath

from .. import get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")
EXAMPLE_DUPLICATE_ENTRY_BIB = get_resource("example_duplicate_entry.bib", "commands")
EXAMPLE_DUPLICATE_ENTRY_YAML = get_resource("example_duplicate_entry.yaml", "commands")
EXAMPLE_MULTI_FILE_ENTRY_BIB = get_resource("example_multi_file_entry.bib", "commands")
EXAMPLE_MULTI_FILE_ENTRY_YAML = get_resource("example_multi_file_entry.yaml", "commands")

if TYPE_CHECKING:
    import cobib.commands


class TestAddCommand(CommandTest, TUITest):
    """Tests for coBib's AddCommand."""

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return AddCommand

    def _assert(self, extra_filename: str) -> None:
        """Common assertion utility method.

        Args:
            extra_filename: path to an additional filename whose contents are to be added to the
                expected lines.
        """
        # compare with reference file
        with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as expected:
            true_lines = expected.readlines()
        with open(extra_filename, "r", encoding="utf-8") as extra:
            true_lines += extra.readlines()
        with open(config.database.file, "r", encoding="utf-8") as file:
            # we use zip_longest to ensure that we don't have more than we expect
            for line, truth in zip_longest(file, true_lines):
                assert line == truth

    def _assert_entry(self, label: str, **kwargs) -> None:  # type: ignore
        """An additional assertion utility to check specific entry fields.

        Args:
            label: the label of the entry.
            kwargs: additional keyword arguments whose contents are checked against the Entry's
                `data contents.
        """
        entry = Database()[label]
        for key, value in kwargs.items():
            assert entry.data.get(key, None) == value

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["more_args", "entry_kwargs"],
        [
            [[], {}],
            [
                ["-f", "test/debug.py"],
                {"file": [str(RelPath("test/debug.py"))]},
            ],
            [["-l", "dummy_label"], {}],
            [["tag"], {"tags": ["tag"]}],
            [["tag", "tag2"], {"tags": ["tag", "tag2"]}],
        ],
    )
    def test_command(self, setup: Any, more_args: List[str], entry_kwargs: Dict[str, Any]) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            more_args: additional arguments to be passed to the command.
            entry_kwargs: the expected contents of the resulting `Entry`.
        """
        git = setup.get("git", False)

        try:
            label = more_args[more_args.index("-l") + 1]
        except ValueError:
            label = "example_multi_file_entry"
        args = ["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB] + more_args

        AddCommand().execute(args)

        assert Database()[label]

        if entry_kwargs or label != "example_multi_file_entry":
            self._assert_entry(label, **entry_kwargs)
        else:
            # only when we don't use extra arguments the files will match
            self._assert(EXAMPLE_MULTI_FILE_ENTRY_YAML)

        if git:
            # assert the git commit message
            # Note: we do not assert the arguments, because they depend on the available parsers
            self.assert_git_commit_message("add", None)

    def test_add_new_entry(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test adding a new plain entry.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        AddCommand().execute(["-l", "dummy"])
        assert (
            "cobib.commands.add",
            30,
            "No input to parse. Creating new entry 'dummy' manually.",
        ) in caplog.record_tuples

        with open(config.database.file, "r", encoding="utf-8") as file:
            lines = file.readlines()
            dummy_start = lines.index("dummy:\n")
            assert dummy_start > 0
            assert lines[dummy_start - 1] == "---\n"
            assert lines[dummy_start + 1] == "  ENTRYTYPE: article\n"
            assert lines[dummy_start + 2] == "...\n"

    @pytest.mark.parametrize("folder", [None, "."])
    def test_add_with_download(
        self, folder: Optional[str], setup: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test adding a new entry with an associated file automatically downloaded.

        Args:
            folder: the folder for the downloaded file.
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            capsys: the built-in pytest fixture.
        """
        path = RelPath(f"{'/tmp' if folder is None else folder}/Cao2018.pdf")
        try:
            # ensure file does not exist yet
            os.remove(path.path)
        except FileNotFoundError:
            pass
        try:
            args = ["-a", "1812.09976"]
            if folder:
                args += ["-p", folder]
            AddCommand().execute(args)
            entry = Database()["Cao2018"]
            assert entry.label == "Cao2018"
            assert entry.data["archivePrefix"] == "arXiv"
            assert entry.data["arxivid"].startswith("1812.09976")
            assert "_download" not in entry.data.keys()
            assert f"Successfully downloaded {path}" in capsys.readouterr().out
            assert os.path.exists(path.path)
        finally:
            try:
                os.remove(path.path)
            except FileNotFoundError:
                pass

    def test_add_skip_download(self, setup: Any) -> None:
        """Test adding a new entry and skipping the automatic download.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        path = RelPath("/tmp/Cao2018.pdf")
        try:
            args = ["-a", "1812.09976", "--skip-download"]
            AddCommand().execute(args)
            entry = Database()["Cao2018"]
            assert entry.label == "Cao2018"
            assert entry.data["archivePrefix"] == "arXiv"
            assert entry.data["arxivid"].startswith("1812.09976")
            assert "_download" not in entry.data.keys()
            assert not os.path.exists(path.path)
        finally:
            try:
                os.remove(path.path)
            except FileNotFoundError:
                pass

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_add_with_update(self, setup: Any) -> None:
        """Test update option of AddCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        git = setup.get("git", False)
        AddCommand().execute(["-a", "1812.09976", "--skip-download"])

        # assert initial state
        entry = Database()["Cao2018"]

        assert entry.data["author"].startswith("Yudong Cao")
        assert entry.data["title"].startswith("Quantum Chemistry in the Age of Quantum Computing")
        assert entry.data["arxivid"].startswith("1812.09976")
        assert entry.data["doi"] == "10.1021/acs.chemrev.8b00803"
        assert entry.data["primaryClass"] == "quant-ph"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["abstract"] != ""
        assert entry.data["year"] == 2018

        assert "journal" not in entry.data.keys()
        assert "month" not in entry.data.keys()
        assert "number" not in entry.data.keys()
        assert "pages" not in entry.data.keys()
        assert "volume" not in entry.data.keys()

        args = ["-d", "10.1021/acs.chemrev.8b00803", "-l", "Cao2018", "--skip-download", "--update"]
        AddCommand().execute(args)

        # assert final state
        entry = Database()["Cao2018"]

        assert entry.data["author"].startswith("Yudong Cao")
        assert entry.data["title"].startswith("Quantum Chemistry in the Age of Quantum Computing")
        assert entry.data["arxivid"].startswith("1812.09976")
        assert entry.data["primaryClass"] == "quant-ph"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["abstract"] != ""

        assert entry.data["journal"] == "Chemical Reviews"
        assert entry.data["doi"] == "10.1021/acs.chemrev.8b00803"
        assert entry.data["month"] == "aug"
        assert entry.data["number"] == 19
        assert entry.data["pages"] == "10856--10915"
        assert entry.data["volume"] == 119
        assert entry.data["year"] == 2019

        if git:
            # assert the git commit message
            # Note: we do not assert the arguments, because they depend on the available parsers
            self.assert_git_commit_message("add", None)

    def test_skip_manual_add_if_exists(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test manual addition is skipped if the label exists already.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        AddCommand().execute(["-l", "einstein"])
        assert (
            "cobib.commands.add",
            30,
            "You tried to add a new entry 'einstein' which already exists!",
        ) in caplog.record_tuples
        assert (
            "cobib.commands.add",
            30,
            "Please use `cobib edit einstein` instead!",
        ) in caplog.record_tuples

    def test_continue_after_skip_exists(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test entry addition continues after skipping over existing entry.

        Regression test against #83

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        with tempfile.NamedTemporaryFile("w") as file:
            with open(EXAMPLE_DUPLICATE_ENTRY_BIB, "r", encoding="utf-8") as existing:
                file.writelines(existing.readlines())
            file.writelines(["@article{dummy,\nauthor = {Dummy},\n}"])
            file.flush()
            AddCommand().execute(["--skip-existing", "-b", file.name])
        assert (
            "cobib.commands.add",
            30,
            "You tried to add a new entry 'einstein' which already exists!",
        ) in caplog.record_tuples
        assert (
            "cobib.commands.add",
            30,
            "Please use `cobib edit einstein` instead!",
        ) in caplog.record_tuples
        assert (
            "cobib.database.database",
            10,
            "Updating entry dummy",
        ) in caplog.record_tuples

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label and any other input.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        AddCommand().execute([""])
        assert (
            "cobib.commands.add",
            40,
            "Neither an input to parse nor a label for manual creation specified!",
        ) in caplog.record_tuples

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_overwrite_label(self, setup: Any) -> None:
        """Test add command while specifying a label manually.

        Regression test against #4.

        The duplicate entry has been adapted to also assert the elongation of Journal names.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        config.utils.journal_abbreviations = [("Annalen der Physik", "Ann. Phys.")]
        git = setup.get("git", False)
        # add potentially duplicate entry
        AddCommand().execute(["-b", EXAMPLE_DUPLICATE_ENTRY_BIB, "--label", "duplicate_resolver"])

        assert Database()["duplicate_resolver"]

        self._assert(EXAMPLE_DUPLICATE_ENTRY_YAML)

        if git:
            # assert the git commit message
            self.assert_git_commit_message("add", None)

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_configured_label_default(self, setup: Any) -> None:
        """Test add command when a `label_default` is pre-configured.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        config.database.format.label_default = "{author.split()[1]}{year}"
        git = setup.get("git", False)

        AddCommand().execute(["-b", EXAMPLE_DUPLICATE_ENTRY_BIB])

        assert Database()["Einstein1905"]

        if git:
            # assert the git commit message
            self.assert_git_commit_message("add", None)

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    def test_disambiguate_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test label disambiguation if the provided one already exists.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        AddCommand().execute(["-b", EXAMPLE_DUPLICATE_ENTRY_BIB])

        assert (
            "cobib.commands.add",
            30,
            "You tried to add a new entry 'einstein' which already exists!",
        ) in caplog.record_tuples
        assert (
            "cobib.commands.add",
            30,
            "The label will be disambiguated based on the configuration option: "
            "config.database.format.label_suffix",
        ) in caplog.record_tuples

        assert Database()["einstein_a"]

        if git:
            # assert the git commit message
            self.assert_git_commit_message("add", None)

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
        ],
        indirect=["setup"],
    )
    # other variants are already covered by test_command
    def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        self.run_module(monkeypatch, "main", ["cobib", "add", "-b", EXAMPLE_MULTI_FILE_ENTRY_BIB])
        self._assert(EXAMPLE_MULTI_FILE_ENTRY_YAML)

    def test_tui(self, setup: Any) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            self._assert(EXAMPLE_MULTI_FILE_ENTRY_YAML)

            assert "example_multi_file_entry" in screen.display[1]

            expected_log = [
                ("cobib.commands.add", 10, "Add command triggered from TUI."),
                ("cobib.commands.add", 10, "Starting Add command."),
                (
                    "cobib.commands.add",
                    10,
                    "Adding entries from bibtex: '" + EXAMPLE_MULTI_FILE_ENTRY_BIB + "'.",
                ),
                ("cobib.commands.add", 20, "'example_multi_file_entry' was added to the database."),
                ("cobib.commands.add", 10, "Updating list after Add command."),
            ]
            assert [log for log in logs if log[0] == "cobib.commands.add"] == expected_log

        keys = "a-b " + EXAMPLE_MULTI_FILE_ENTRY_BIB + "\n"
        self.run_tui(keys, assertion, {})

    def test_event_pre_add_command(self, setup: Any) -> None:
        """Tests the PreAddCommand event."""

        @Event.PreAddCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.label = "dummy"

        assert Event.PreAddCommand.validate()

        AddCommand().execute(["-b", EXAMPLE_DUPLICATE_ENTRY_BIB])

        assert "dummy" in Database().keys()

    def test_event_post_add_command(self, setup: Any) -> None:
        """Tests the PostAddCommand event."""

        @Event.PostAddCommand.subscribe
        def hook(new_entries: Dict[str, Entry]) -> None:
            new_entries["dummy"] = new_entries.pop("einstein_a")

        assert Event.PostAddCommand.validate()

        AddCommand().execute(["-b", EXAMPLE_DUPLICATE_ENTRY_BIB])

        assert "dummy" in Database().keys()
