"""Tests for coBib's DeleteCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import contextlib
import tempfile
from io import StringIO
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Type

import pytest
from typing_extensions import override

from cobib.commands import DeleteCommand
from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .. import MockStdin, get_resource
from .command_test import CommandTest

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class TestDeleteCommand(CommandTest):
    """Tests for coBib's DeleteCommand."""

    @override
    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        return DeleteCommand

    @pytest.fixture
    def post_setup(
        self, monkeypatch: pytest.MonkeyPatch, request: _pytest.fixtures.SubRequest
    ) -> Generator[Dict[str, Any], None, None]:
        """Additional setup instructions.

        Args:
            monkeypatch: the built-in pytest fixture.
            request: a pytest sub-request providing access to nested parameters.

        Yields:
            The internally used parameters for potential later re-use during the actual test.
        """
        if not hasattr(request, "param"):
            # use default settings
            request.param = {"stdin_list": None}

        monkeypatch.setattr("sys.stdin", MockStdin(request.param.get("stdin_list", None)))

        yield request.param

    def _assert(self, labels: List[str]) -> None:
        """Common assertion utility method.

        Args:
            labels: the list of labels to be deleted.
        """
        bib = Database()

        for label in labels:
            assert bib.get(label, None) is None

        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(get_resource("example_literature.yaml"), "r", encoding="utf-8") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    assert line == truth
                with pytest.raises(StopIteration):
                    next(file)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "setup",
        [
            {"git": False},
            {"git": True},
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["labels", "skip_commit"],
        [
            [["knuthwebsite"], False],
            [["knuthwebsite", "latexcompanion"], False],
            # non-existent labels should not cause any problems (but skip git check)
            [["dummy"], True],
            [["dummy", "knuthwebsite"], False],
        ],
    )
    async def test_command(self, setup: Any, labels: List[str], skip_commit: bool) -> None:
        # pylint: disable=invalid-overridden-method
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            labels: the list of labels to be deleted.
            skip_commit: whether to skip asserting the git commit message.
        """
        git = setup.get("git", False)

        # delete some data (for testing simplicity we delete the entries from the end)
        await DeleteCommand(*labels).execute()
        self._assert(labels)

        if git and not skip_commit:
            # assert the git commit message
            self.assert_git_commit_message("delete", {"labels": labels, "preserve_files": None})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["labels", "post_setup"],
        [
            [["knuthwebsite"], {"stdin_list": ["y"]}],
            [["knuthwebsite"], {"stdin_list": ["n"]}],
            [["knuthwebsite", "latexcompanion"], {"stdin_list": ["y", "y"]}],
            [["knuthwebsite", "latexcompanion"], {"stdin_list": ["n", "n"]}],
            [["knuthwebsite", "latexcompanion"], {"stdin_list": ["y", "n"]}],
            [["knuthwebsite", "latexcompanion"], {"stdin_list": ["n", "y"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_confirmation_prompt(
        self, setup: Any, post_setup: Any, labels: List[str]
    ) -> None:
        """TODO."""
        config.commands.delete.confirm = True

        choices = post_setup.get("stdin_list", False)

        await DeleteCommand(*labels).execute()

        if "n" in choices:
            bib = Database()

            for label, choice in zip(labels, choices):
                entry = bib.get(label, None)
                if choice == "y":
                    assert entry is None
                else:
                    assert entry is not None
        else:
            self._assert(labels)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("preserve_files", [None, True, False])
    @pytest.mark.parametrize("config_overwrite", [True, False])
    async def test_remove_associated_file(
        self, setup: Any, preserve_files: bool, config_overwrite: bool
    ) -> None:
        """Test removing associated files.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            preserve_files: argument to `DeleteCommand`.
            config_overwrite: what to overwrite `config.commands.delete.preserve_files` with.
        """
        config.commands.delete.preserve_files = config_overwrite

        should_preserve = config_overwrite
        if preserve_files is not None:
            should_preserve = preserve_files

        with tempfile.TemporaryDirectory() as tmpdirname:
            path = RelPath(tmpdirname + "/dummy.pdf")
            open(path.path, "w", encoding="utf-8").close()  # pylint: disable=consider-using-with

            Database()["knuthwebsite"].file = str(path)

            args = ["knuthwebsite"]
            if preserve_files is not None:
                args += [f"--{'' if preserve_files else 'no-'}preserve-files"]
            await DeleteCommand(*args).execute()

            assert path.path.exists() is should_preserve

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "setup",
        [{"git": False}],
        indirect=["setup"],
    )
    async def test_base_cmd_insufficient_git(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test warning is raised by BaseCommand during insufficient git-configuration.

        While this is technically not related to the DeleteCommand, this is one of the faster
        commands to test this on.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        config.database.git = True

        await DeleteCommand("knuthwebsite").execute()
        self._assert(["knuthwebsite"])

        assert (
            "cobib.commands.base_command",
            30,
            "You have configured coBib to track your database with git."
            "\nPlease run `cobib init --git`, to initialize this tracking.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["labels"],
        [
            [["knuthwebsite"]],
            [["knuthwebsite", "latexcompanion"]],
        ],
    )
    # other variants are already covered by test_command
    async def test_cmdline(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, labels: List[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            labels: the list of labels to be deleted.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "delete"] + labels)
        self._assert(labels)

    @pytest.mark.asyncio
    async def test_event_pre_delete_command(self, setup: Any) -> None:
        """Tests the PreDeleteCommand event."""

        @Event.PreDeleteCommand.subscribe
        def hook(command: DeleteCommand) -> None:
            command.largs.labels = ["einstein"]

        assert Event.PreDeleteCommand.validate()

        await DeleteCommand("knuthwebsite").execute()

        assert "einstein" not in Database().keys()
        assert "knuthwebsite" in Database().keys()

    @pytest.mark.asyncio
    async def test_event_post_delete_command(self, setup: Any) -> None:
        """Tests the PostDeleteCommand event."""

        @Event.PostDeleteCommand.subscribe
        def hook(command: DeleteCommand) -> None:
            for label in command.deleted_entries:
                print(f"WARNING: deleted entry '{label}'")

        with contextlib.redirect_stdout(StringIO()) as out:
            await DeleteCommand("knuthwebsite").execute()

        assert Event.PostDeleteCommand.validate()

        assert out.getvalue().strip() == "WARNING: deleted entry 'knuthwebsite'"
