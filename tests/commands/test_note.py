"""Tests for coBib's NoteCommand."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import pytest
from rich.syntax import Syntax
from typing_extensions import override

from cobib.commands import NoteCommand
from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

from .. import MockStdin
from .command_test import CommandTest

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class TestNoteCommand(CommandTest):
    """Tests for coBib's NoteCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return NoteCommand

    @pytest.fixture
    def post_setup(
        self, monkeypatch: pytest.MonkeyPatch, request: _pytest.fixtures.SubRequest
    ) -> Generator[dict[str, Any], None, None]:
        """Additional setup instructions.

        Args:
            monkeypatch: the built-in pytest fixture.
            request: a pytest sub-request providing access to nested parameters.

        Yields:
            The internally used parameters for potential later re-use during the actual test.
        """
        if not hasattr(request, "param"):
            # use default settings
            request.param = {"stdin_list": None, "setup_notes": []}

        monkeypatch.setattr("sys.stdin", MockStdin(request.param.get("stdin_list", None)))

        db_path = RelPath(config.database.file).path.parent

        apply_inline = request.param.get("apply_inline", False)
        paths_to_unlink = []
        for label in request.param.get("setup_notes", []):
            path = Path(f"{db_path}/{label}.{config.commands.note.default_filetype}")
            paths_to_unlink.append(path)
            with open(path, "w", encoding="utf-8") as file:
                file.write(f"Dummy note for the '{label}' entry.")

            if apply_inline:
                NoteCommand(label, "_inline").execute()

        yield request.param

        for path in paths_to_unlink:
            path.unlink(missing_ok=True)

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        # Note: when using a filter, no non-existent label can occur
        args = ["dummy", "show"]
        NoteCommand(*args).execute()
        assert (
            "cobib.commands.note",
            40,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    def test_skip_missing_note_path(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test skipping all further actions upon missing note file.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        args = ["einstein", "edit"]
        NoteCommand(*args).execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.note"]

        # check common log
        expected_log = [
            ("cobib.commands.note", 10, "Starting Note command."),
            ("cobib.commands.note", 10, 'Starting editor "cat".'),
            (
                "cobib.commands.note",
                40,
                'The note editing using "cat" failed with the following error code: 256',
            ),
            (
                "cobib.commands.note",
                30,
                "Could not find the note file associated with 'einstein'. Skipping any further "
                "actions. Check the following path if you believe this to be an error: "
                f"'{RelPath(self.COBIB_TEST_DIR)}/einstein.txt'",
            ),
        ]

        assert true_log == expected_log

    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"setup_notes": ["einstein"]}],
        ],
        indirect=["post_setup"],
    )
    def test_command_edit(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the `edit` action of the note command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        label = "einstein"
        action = "edit"
        cmd = NoteCommand(label, action)
        cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.note"]

        expected_log = [
            ("cobib.commands.note", 10, "Starting Note command."),
            ("cobib.commands.note", 10, 'Starting editor "cat".'),
            ("cobib.commands.note", 10, "Editor finished successfully."),
            ("cobib.commands.note", 20, "The note of 'einstein' was successfully edited."),
        ]

        assert true_log == expected_log

        assert cmd.note_content is None

        git = setup.get("git", False)
        if git:
            # assert the git commit message
            self.assert_git_commit_message("note", {"label": label, "action": action})

    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"setup_notes": ["einstein"]}],
        ],
        indirect=["post_setup"],
    )
    def test_command_inline(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the `_inline` action of the note command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        label = "einstein"
        action = "_inline"
        cmd = NoteCommand(label, action)
        cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.note"]

        expected_log = [
            ("cobib.commands.note", 10, "Starting Note command."),
            (
                "cobib.commands.note",
                20,
                "An inline note edit was performed. This command is merely executed to ensure it "
                "gets committed into any git history tracking.",
            ),
            ("cobib.commands.note", 20, "The note of 'einstein' was successfully edited."),
        ]

        assert true_log == expected_log

        assert cmd.note_content is None

        git = setup.get("git", False)
        if git:
            # assert the git commit message
            self.assert_git_commit_message("note", {"label": label, "action": action})

    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"setup_notes": ["einstein"], "apply_inline": False}],
            [{"setup_notes": ["einstein"], "apply_inline": True}],
        ],
        indirect=["post_setup"],
    )
    def test_command_delete(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the `delete` action of the note command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        label = "einstein"
        action = "delete"
        cmd = NoteCommand(label, action)
        cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.note"]

        expected_log = [
            ("cobib.commands.note", 10, "Starting Note command."),
            ("cobib.commands.note", 20, "The note of 'einstein' was successfully deleted."),
        ]

        apply_inline = post_setup.get("apply_inline", False)
        if not apply_inline:
            expected_log.insert(
                1,
                (
                    "cobib.commands.note",
                    30,
                    "The entry 'einstein' did not have an associated note!",
                ),
            )

        assert true_log == expected_log

        assert cmd.note_content is None

        git = setup.get("git", False)
        if git:
            # assert the git commit message
            self.assert_git_commit_message("note", {"label": label, "action": action})

    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"setup_notes": []}],
            [{"setup_notes": ["einstein"]}],
        ],
        indirect=["post_setup"],
    )
    def test_render_rich(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the rich rendering and associated `show` action of the note command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        setup_notes = post_setup.get("setup_notes", [])
        cmd = NoteCommand("einstein", "show")
        cmd.execute()

        renderable = cmd.render_rich()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.note"]

        expected_log = [
            ("cobib.commands.note", 10, "Starting Note command."),
            ("cobib.commands.note", 20, "The note of 'einstein' was successfully shown."),
        ]

        if len(setup_notes) == 0:
            expected_log.insert(
                1,
                (
                    "cobib.commands.note",
                    40,
                    "Encountered the following error while trying to read the note of the entry "
                    "'einstein':",
                ),
            )

            expected_log.insert(
                2,
                (
                    "cobib.commands.note",
                    40,
                    "[Errno 2] No such file or directory: "
                    f"'{RelPath(self.COBIB_TEST_DIR).path}/einstein.txt'",
                ),
            )

            assert renderable is None
        else:
            assert cmd.note_content == "Dummy note for the 'einstein' entry."

            assert isinstance(renderable, Syntax)
            assert renderable.code == cmd.note_content
            assert renderable._lexer == "txt"

        assert true_log == expected_log

    def test_event_pre_note_command(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PreNoteCommand event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """

        @Event.PreNoteCommand.subscribe
        def hook(command: NoteCommand) -> None:
            command.largs.action = "dummy"

        assert Event.PreNoteCommand.validate()

        cmd = NoteCommand("einstein", "show")
        cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.note"]

        expected_log = [
            ("cobib.commands.note", 10, "Starting Note command."),
            (
                "cobib.commands.note",
                30,
                "Encountered unexpected command action: 'dummy'! Don't know what to do!",
            ),
            ("cobib.commands.note", 20, "The note of 'einstein' was successfully ignored."),
        ]

        assert true_log == expected_log

    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"setup_notes": ["einstein"]}],
        ],
        indirect=["post_setup"],
    )
    def test_event_post_note_command(self, setup: Any, post_setup: Any) -> None:
        """Tests the PostNoteCommand event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
        """

        @Event.PostNoteCommand.subscribe
        def hook(command: NoteCommand) -> None:
            command.note_content = "Replaced note content!"

        assert Event.PostNoteCommand.validate()

        cmd = NoteCommand("einstein", "show")
        cmd.execute()

        assert cmd.note_content == "Replaced note content!"
