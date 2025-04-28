"""Tests for coBib's ReviewCommand."""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from io import StringIO
from shutil import rmtree
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ReviewCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import MockStdin
from .command_test import CommandTest

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class TestReviewCommand(CommandTest):
    """Tests for coBib's ReviewCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ReviewCommand

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
            request.param = {"stdin_list": None}

        monkeypatch.setattr("sys.stdin", MockStdin(request.param.get("stdin_list", None)))

        config.theme.syntax.line_numbers = False

        yield request.param

    def _assert(  # type: ignore[no-untyped-def]
        self, output: str, logs: list[tuple[str, int, str]] | None = None, **kwargs
    ) -> None:
        """Common assertion utility method.

        Args:
            output: the list of lines printed to `sys.stdout`.
            logs: the list of logged messages.
            kwargs: additional test-specific keyword arguments.
        """
        expected_out = [
            "---",
            "einstein:",
            "  ENTRYTYPE: article",
            "  author:",
            "  - first: Albert",
            "    last: Einstein",
            "  doi: http://dx.doi.org/10.1002/andp.19053221004",
            "  journal: Annalen der Physik",
            "  number: 10",
            "  pages: 891--921",
            '  title: Zur Elektrodynamik bewegter K{\\"o}rper',
            "  volume: 322",
            "  year: 1905",
            "...",
            "",
            "What action what you like to perform? [done/skip/edit/inline/finish/help]: ",
        ]

        expected_log = [
            ("cobib.commands.review", 10, "Starting Review command."),
            ("cobib.commands.review", 10, "Gathering filtered list of entries to be reviewed."),
            ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
            ("cobib.commands.review", 20, "Finishing review early."),
        ]

        context = kwargs.get("context", False)
        if context:
            expected_log.insert(
                3,
                (
                    "cobib.commands.review",
                    10,
                    "Context has been requested so the fields are not filtered.",
                ),
            )

        stdin_list = kwargs.get("stdin_list", [])
        if "help" in stdin_list:
            expected_out += expected_out.copy()
            expected_out[15] += "You may perform any of the following actions:"
            extra_out = [
                "    edit: open the current entry for editing",
                "    skip: skip the current entry",
                "    done: mark the current entry as done",
                "  finish: finish the review early",
                "  inline: EXPERIMENTAL edit a field in-line",
            ]
            for line in reversed(extra_out):
                expected_out.insert(16, line)

            expected_log.insert(3, ("cobib.commands.review", 10, "User requested help."))

        assert output.replace("  ", " ") == " ".join(expected_out).replace("  ", " ")
        if logs is not None:
            assert logs == expected_log

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["finish"]}],
            [{"stdin_list": ["help", "finish"]}],
        ],
        indirect=["post_setup"],
    )
    # other variants covered in separate tests below
    async def test_command(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        cmd = ReviewCommand()
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]
        true_out = " ".join(capsys.readouterr().out.split("\n"))

        self._assert(true_out, true_log, **post_setup)

        if git:
            # assert the git commit message
            self.assert_git_commit_message(
                "review",
                {
                    "field": [],
                    "context": False,
                    "resume": None,
                    "done": [],
                    "selection": False,
                    "filter": [],
                },
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["finish"]}],
        ],
        indirect=["post_setup"],
    )
    # other variants covered in separate tests below
    async def test_cmdline(
        self,
        setup: Any,
        post_setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            monkeypatch: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "review"])

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]
        true_out = " ".join(capsys.readouterr().out.split("\n"))

        self._assert(true_out, true_log)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["edit", "done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_edit(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test the editing action.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        try:
            config.commands.edit.editor = "sed -i 's/Annalen der Physik/Annals of Physics/'"

            cmd = ReviewCommand("-s", "--", "einstein")
            await cmd.execute()

            true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]

            assert Database()["einstein"].data["journal"] == "Annals of Physics"

            expected_log = [
                ("cobib.commands.review", 10, "Starting Review command."),
                (
                    "cobib.commands.review",
                    20,
                    "Selection given. Interpreting `filter` as a list of labels",
                ),
                ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
                ("cobib.commands.review", 20, "Marking entry 'einstein' as done."),
            ]

            assert true_log == expected_log

            if git:
                # assert the git commit message
                self.assert_git_commit_message(
                    "review",
                    {
                        "field": [],
                        "context": False,
                        "resume": None,
                        "done": ["einstein"],
                        "selection": True,
                        "filter": ["einstein"],
                    },
                )

        finally:
            config.defaults()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["edit", "done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_edit_no_changes(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test the editing action when no changes are made.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        cmd = ReviewCommand("-s", "--", "einstein")
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]

        expected_log = [
            ("cobib.commands.review", 10, "Starting Review command."),
            (
                "cobib.commands.review",
                20,
                "Selection given. Interpreting `filter` as a list of labels",
            ),
            ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
            ("cobib.commands.review", 20, "No changes detected."),
            ("cobib.commands.review", 20, "Marking entry 'einstein' as done."),
        ]

        assert true_log == expected_log

        if git:
            # assert the git commit message
            # NOTE: this is an empty commit and only works as long as --allow-empty is set
            self.assert_git_commit_message(
                "review",
                {
                    "field": [],
                    "context": False,
                    "resume": None,
                    "done": ["einstein"],
                    "selection": True,
                    "filter": ["einstein"],
                },
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["edit", "done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_edit_rename_disallowed(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that renaming is not allowed during reviewing.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        try:
            config.commands.edit.editor = "sed -i 's/einstein:/dummy:/'"

            cmd = ReviewCommand("-s", "--", "einstein")
            await cmd.execute()

            true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]

            bib = Database()
            assert "einstein" in bib.keys()
            assert "dummy" not in bib.keys()

            expected_log = [
                ("cobib.commands.review", 10, "Starting Review command."),
                (
                    "cobib.commands.review",
                    20,
                    "Selection given. Interpreting `filter` as a list of labels",
                ),
                ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
                (
                    "cobib.commands.review",
                    40,
                    "Renaming entries as part of the review process is not supported!",
                ),
                ("cobib.commands.review", 20, "Marking entry 'einstein' as done."),
            ]

            assert true_log == expected_log

        finally:
            config.defaults()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["skip"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_skip(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test the skipping action.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        cmd = ReviewCommand("-s", "--", "einstein")
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]

        expected_log = [
            ("cobib.commands.review", 10, "Starting Review command."),
            (
                "cobib.commands.review",
                20,
                "Selection given. Interpreting `filter` as a list of labels",
            ),
            ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
            ("cobib.commands.review", 20, "Skipping entry 'einstein'."),
        ]

        assert true_log == expected_log

        if git:
            # assert the git commit message
            # NOTE: this is an empty commit and only works as long as --allow-empty is set
            self.assert_git_commit_message(
                "review",
                {
                    "field": [],
                    "context": False,
                    "resume": None,
                    "done": [],
                    "selection": True,
                    "filter": ["einstein"],
                },
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["done", "finish", "done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_resume(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test the resume action.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        cmd = ReviewCommand("--", "--label", "einstein")
        await cmd.execute()

        cmd = ReviewCommand("--resume", "HEAD")
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]

        expected_log = [
            ("cobib.commands.review", 10, "Starting Review command."),
            ("cobib.commands.review", 10, "Gathering filtered list of entries to be reviewed."),
            ("cobib.commands.review", 10, "Starting review of entry 'latexcompanion'"),
            ("cobib.commands.review", 20, "Marking entry 'latexcompanion' as done."),
            ("cobib.commands.review", 10, "Starting review of entry 'knuthwebsite'"),
            ("cobib.commands.review", 20, "Finishing review early."),
            ("cobib.commands.review", 20, "Trying to resume review from HEAD."),
            ("cobib.commands.review", 20, "Found the git-commit from which to resume."),
            ("cobib.commands.review", 10, "Starting Review command."),
            ("cobib.commands.review", 10, "Gathering filtered list of entries to be reviewed."),
            ("cobib.commands.review", 10, "Starting review of entry 'knuthwebsite'"),
            ("cobib.commands.review", 20, "Marking entry 'knuthwebsite' as done."),
        ]

        assert true_log == expected_log

        # assert the git commit message
        self.assert_git_commit_message(
            "review",
            {
                "field": [],
                "context": False,
                "resume": "HEAD",
                "done": ["latexcompanion", "knuthwebsite"],
                "selection": False,
                "filter": ["--label", "einstein"],
            },
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["sha", "setup"],
        [
            ["HEAD", {"git": False}],
            ["HEAD", {"git": True}],
            ["test", {"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_command_resume_graceful(
        self,
        setup: Any,
        caplog: pytest.LogCaptureFixture,
        sha: str,
    ) -> None:
        """Test the graceful handling of the resume action.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
            sha: the git commit sha to use.
        """
        git = setup.get("git", False)

        if not git:
            await ReviewCommand("--resume", sha).execute()
            for source, level, message in caplog.record_tuples:
                if ("cobib.commands.review", logging.ERROR) == (
                    source,
                    level,
                ) and "git-tracking" in message:
                    break
            else:
                pytest.fail("No Error logged from ReviewCommand.")
            return

        cmd = ReviewCommand("--resume", sha)
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]

        expected_log = [("cobib.commands.review", 20, f"Trying to resume review from {sha}.")]
        if sha == "HEAD":
            expected_log.append(
                (
                    "cobib.commands.review",
                    40,
                    "Could not extract arguments from the trimmed message: ''",
                )
            )
        elif sha == "test":
            expected_log.append(
                ("cobib.commands.review", 40, "Could not find the requested git commit: 'test'")
            )

        assert true_log == expected_log

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_warn_insufficient_setup(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test warning in case of insufficient setup.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        rmtree(self.COBIB_TEST_DIR_GIT)
        await ReviewCommand("--resume", "HEAD").execute()
        for source, level, message in caplog.record_tuples:
            if ("cobib.commands.review", logging.ERROR) == (
                source,
                level,
            ) and "configured, but not initialized" in message:
                break
        else:
            pytest.fail("No Error logged from ReviewCommand.")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["edit", "done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_fields(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test the command with specific fields to review.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        try:
            config.commands.edit.editor = "sed -i 's/1905/1900/'"

            cmd = ReviewCommand("tags", "year", "-s", "--", "einstein")
            await cmd.execute()

            true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]
            true_out = " ".join(capsys.readouterr().out.split("\n"))

            assert Database()["einstein"].data["year"] == 1900

            expected_out = [
                "---",
                "einstein:",
                "  year: 1905",
                "...",
                "",
                "What action what you like to perform?",
                "[context/done/skip/edit/inline/finish/help]: ---",
                "einstein:",
                "  year: 1900",
                "...",
                "",
                "What action what you like to perform?",
                "[context/done/skip/edit/inline/finish/help]: ",
            ]

            expected_log = [
                ("cobib.commands.review", 10, "Starting Review command."),
                (
                    "cobib.commands.review",
                    20,
                    "Selection given. Interpreting `filter` as a list of labels",
                ),
                ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
                (
                    "cobib.commands.review",
                    10,
                    "Limiting the review to the requested fields: '['tags', 'year']'",
                ),
                (
                    "cobib.commands.review",
                    10,
                    "Limiting the review to the requested fields: '['tags', 'year']'",
                ),
                ("cobib.commands.review", 20, "Marking entry 'einstein' as done."),
            ]

            assert true_out.replace("  ", " ") == " ".join(expected_out).replace("  ", " ")
            assert true_log == expected_log

            if git:
                # assert the git commit message
                self.assert_git_commit_message(
                    "review",
                    {
                        "field": ["tags", "year"],
                        "context": False,
                        "resume": None,
                        "done": ["einstein"],
                        "selection": True,
                        "filter": ["einstein"],
                    },
                )

        finally:
            config.defaults()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["context", "post_setup"],
        [
            [False, {"stdin_list": ["context", "done", "finish"]}],
            [True, {"stdin_list": ["finish"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_context(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
        context: bool,
    ) -> None:
        """Test the context option.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            context: whether to provide the `--context` argument.
        """
        git = setup.get("git", False)

        args = ["year"]
        if context:
            args.append("--context")
        cmd = ReviewCommand(*args)
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]
        true_out = " ".join(capsys.readouterr().out.split("\n"))

        if context:
            self._assert(true_out, true_log, context=context)
        else:
            expected_out = [
                "---",
                "einstein:",
                "  year: 1905",
                "...",
                "",
                "What action what you like to perform?",
                "[context/done/skip/edit/inline/finish/help]: ---",
                "einstein:",
                "  ENTRYTYPE: article",
                "  author:",
                "  - first: Albert",
                "    last: Einstein",
                "  doi: http://dx.doi.org/10.1002/andp.19053221004",
                "  journal: Annalen der Physik",
                "  number: 10",
                "  pages: 891--921",
                '  title: Zur Elektrodynamik bewegter K{\\"o}rper',
                "  volume: 322",
                "  year: 1905",
                "...",
                "",
                "What action what you like to perform? [done/skip/edit/inline/finish/help]: ---",
                "latexcompanion:",
                "  year: 1993",
                "...",
                "",
                "What action what you like to perform?",
                "[context/done/skip/edit/inline/finish/help]: ",
            ]

            expected_log = [
                ("cobib.commands.review", 10, "Starting Review command."),
                ("cobib.commands.review", 10, "Gathering filtered list of entries to be reviewed."),
                ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
                (
                    "cobib.commands.review",
                    10,
                    "Limiting the review to the requested fields: '['year']'",
                ),
                ("cobib.commands.review", 20, "Requesting more context."),
                (
                    "cobib.commands.review",
                    10,
                    "Context has been requested so the fields are not filtered.",
                ),
                ("cobib.commands.review", 20, "Marking entry 'einstein' as done."),
                ("cobib.commands.review", 10, "Starting review of entry 'latexcompanion'"),
                (
                    "cobib.commands.review",
                    10,
                    "Limiting the review to the requested fields: '['year']'",
                ),
                ("cobib.commands.review", 20, "Finishing review early."),
            ]

            assert true_out.replace("  ", " ") == " ".join(expected_out).replace("  ", " ")
            assert true_log == expected_log

        if git:
            # assert the git commit message
            self.assert_git_commit_message(
                "review",
                {
                    "field": ["year"],
                    "context": context,
                    "resume": None,
                    "done": [] if context else ["einstein"],
                    "selection": False,
                    "filter": [],
                },
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["args", "post_setup"],
        [
            [["year"], {"stdin_list": ["inline", "1900", "finish"]}],
            [["year", "tags"], {"stdin_list": ["inline year", "1900", "finish"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command_inline(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
        args: list[str],
    ) -> None:
        """Test the inline action.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            args: the arguments for the command.
        """
        git = setup.get("git", False)

        cmd = ReviewCommand(*args)
        await cmd.execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.review"]
        true_out = " ".join(capsys.readouterr().out.split("\n"))

        assert Database()["einstein"].data["year"] == 1900

        expected_out = [
            "---",
            "einstein:",
            "  year: 1905",
            "...",
            "",
            "What action what you like to perform? ",
            "[context/done/skip/edit/inline/finish/help]: ",
            "WARNING: the inline editing is a highly experimental feature!",
            "Be aware of bugs and proceed with care.",
            "Please report any issues or suggestions online: ",
            "https://gitlab.com/cobib/cobib/-/issues/new",
            "---",
            "einstein:",
            "  year: 1905",
            "...",
            "",
            "Please provide the new value for the field 'year': ---",
            "einstein:",
            "  year: 1900",
            "...",
            "",
            "What action what you like to perform? ",
            "[context/done/skip/edit/inline/finish/help]: ",
        ]

        expected_log = [
            ("cobib.commands.review", 10, "Starting Review command."),
            ("cobib.commands.review", 10, "Gathering filtered list of entries to be reviewed."),
            ("cobib.commands.review", 10, "Starting review of entry 'einstein'"),
            (
                "cobib.commands.review",
                10,
                f"Limiting the review to the requested fields: '{args}'",
            ),
            ("cobib.commands.review", 20, "Editing field 'year' in-line."),
            (
                "cobib.commands.review",
                10,
                f"Limiting the review to the requested fields: '{args}'",
            ),
            ("cobib.commands.review", 20, "Finishing review early."),
        ]

        assert true_out.replace("  ", " ") == " ".join(expected_out).replace("  ", " ")
        assert true_log == expected_log

        if git:
            # assert the git commit message
            self.assert_git_commit_message(
                "review",
                {
                    "field": args,
                    "context": False,
                    "resume": None,
                    "done": [],
                    "selection": False,
                    "filter": [],
                },
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_event_pre_review_command(self, setup: Any, post_setup: Any) -> None:
        """Tests the PreReviewCommand event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
        """

        @Event.PreReviewCommand.subscribe
        def hook(command: ReviewCommand) -> None:
            command.largs.done = ["einstein"]

        assert Event.PreReviewCommand.validate()

        await ReviewCommand("--", "++label", "einstein").execute()

        with contextlib.redirect_stdout(StringIO()) as out:
            await ReviewCommand("--", "++label", "einstein").execute()
            assert out.getvalue() == ""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["done"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_event_post_review_command(self, setup: Any, post_setup: Any) -> None:
        """Tests the PostReviewCommand event.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
        """

        @Event.PostReviewCommand.subscribe
        def hook(command: ReviewCommand) -> None:
            # do some random modification which we can test
            command.reviewed_entries[0].data["number"] += 2

        assert Event.PostReviewCommand.validate()

        await ReviewCommand("--", "++label", "einstein").execute()
        assert Database()["einstein"].data["number"] == 12
