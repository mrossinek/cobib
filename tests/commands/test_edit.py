"""Tests for coBib's EditCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import tempfile
from argparse import Namespace
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Type

import pytest

from cobib.commands import EditCommand
from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.utils.rel_path import RelPath

from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestEditCommand(CommandTest, TUITest):
    """Tests for coBib's EditCommand.

    Note: in order to be able to test this command to at least a minimal degree, the test
    configuration sets the "editor" to be "cat". Thus, no changes will ever actually be made through
    this "editor".
    Nonetheless, this allows us to test the case where no changes are made (obviously), while also
    being able to test that the EditCommand actually writes to the database when (e.g.) the `--add`
    keyword argument is being used.
    """

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return EditCommand

    @staticmethod
    def _assert(
        changes: bool, logs: Optional[List[Tuple[str, int, str]]] = None, label: str = "dummy"
    ) -> None:
        """Common assertion utility method.

        Args:
            changes: whether actual changes were applied.
            logs: the list of logged messages.
            label: the label of the edited `Entry`.
        """
        if changes:
            if logs is not None:
                assert ("cobib.commands.edit", 20, f"'{label}' was successfully edited.") in logs

            with open(config.database.file, "r", encoding="utf-8") as file:
                lines = file.readlines()
                dummy_start = lines.index("dummy:\n")
                assert dummy_start > 0
                assert lines[dummy_start - 1] == "---\n"
                assert lines[dummy_start + 1] == "  ENTRYTYPE: article\n"
                assert lines[dummy_start + 2] == "...\n"
        else:
            if logs is not None:
                assert ("cobib.commands.edit", 20, "No changes detected.") in logs

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["args", "changes"],
        [
            [["einstein"], False],
            [["-a", "dummy"], True],
        ],
    )
    def test_command(
        self, setup: Any, caplog: pytest.LogCaptureFixture, args: List[str], changes: bool
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
            args: the arguments to pass to the command.
            changes: whether actual changes will be applied.
        """
        git = setup.get("git", False)

        EditCommand().execute(args)

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.edit"]

        # check common log
        expected_log = [
            ("cobib.commands.edit", 10, "Starting Edit command."),
            ("cobib.commands.edit", 10, "Creating temporary file."),
            ("cobib.commands.edit", 10, 'Starting editor "cat".'),
            ("cobib.commands.edit", 10, "Editor finished successfully."),
        ]

        assert true_log[0:4] == expected_log
        self._assert(changes=changes, logs=true_log)

        if git and changes:
            # assert the git commit message
            self.assert_git_commit_message(
                "edit", {"label": args[-1], "add": "-a" in args, "preserve_files": False}
            )

    def test_ignore_add_if_label_exists(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test that the `add` argument is ignored if the label already exists.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        EditCommand().execute(["-a", "einstein"])
        assert (
            "cobib.commands.edit",
            30,
            "Entry 'einstein' already exists! Ignoring the `--add` argument.",
        ) in caplog.record_tuples

    @pytest.mark.parametrize("preserve_files", [True, False])
    def test_rename_associated_file(self, setup: Any, preserve_files: bool) -> None:
        """Test removing associated files.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            preserve_files: argument to `DeleteCommand`.
        """
        try:
            config.commands.edit.editor = "sed -i 's/einstein:/dummy:/'"

            with tempfile.TemporaryDirectory() as tmpdirname:
                path = RelPath(tmpdirname + "/einstein.pdf")
                open(  # pylint: disable=consider-using-with
                    path.path, "w", encoding="utf-8"
                ).close()

                Database()["einstein"].file = str(path)

                args = ["einstein"]
                if preserve_files:
                    args.insert(2, "--preserve-files")
                EditCommand().execute(args)
                assert "dummy" in Database().keys()

                target = RelPath(tmpdirname + "/dummy.pdf")
                if preserve_files:
                    assert path.path.exists()
                else:
                    assert target.path.exists()
        finally:
            config.defaults()

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        EditCommand().execute(["dummy"])
        assert (
            "cobib.commands.edit",
            40,
            "No entry with the label 'dummy' could be found.\n"
            "Use `--add` to add a new entry with this label.",
        ) in caplog.record_tuples

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
        ],
        indirect=["setup"],
    )
    def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        self.run_module(monkeypatch, "main", ["cobib", "edit", "-a", "dummy"])
        self._assert(changes=True, logs=None)

    def test_tui(self, setup: Any) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            true_log = [log for log in logs if log[0] == "cobib.commands.edit"]
            self._assert(changes=False, logs=true_log)

        self.run_tui("e", assertion, {})

    def test_event_pre_edit_command(self, setup: Any) -> None:
        """Tests the PreEditCommand event."""

        @Event.PreEditCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.add = True
            largs.label = "dummy"

        assert Event.PreEditCommand.validate()

        EditCommand().execute(["einstein"])

        self._assert(changes=True)

    def test_event_post_edit_command(self, setup: Any) -> None:
        """Tests the PostEditCommand event."""

        @Event.PostEditCommand.subscribe
        def hook(new_entry: Entry) -> None:
            new_entry.data["tags"] = "test"

        assert Event.PostEditCommand.validate()

        EditCommand().execute(["-a", "dummy"])

        assert Database()["dummy"].data["tags"] == "test"
