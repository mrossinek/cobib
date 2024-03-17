"""Tests for coBib's shell helper functions."""

from __future__ import annotations

import logging
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, ClassVar

import pytest
from typing_extensions import override

from cobib.commands import LintCommand
from cobib.config import config
from cobib.utils.rel_path import RelPath
from tests.commands.command_test import CommandTest

from .. import get_resource

if TYPE_CHECKING:
    import cobib.commands

LOGGER = logging.getLogger()


class TestLintDatabase(CommandTest):
    """Tests for the shell helper which lints the users database."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return LintCommand

    REL_PATH = RelPath(get_resource("linting_database.yaml", "commands"))

    EXPECTED: ClassVar[list[str]] = [
        f"{REL_PATH}:5 Parsed the author 'Max Müller' of entry 'dummy' from a string to the "
        "more detailed information. You can consider storing it as such directly.",
        f"{REL_PATH}:6 Converted the field 'file' of entry 'dummy' to a list. You can consider "
        "storing it as such directly.",
        f"{REL_PATH}:7 Converting field 'month' of entry 'dummy' from '8' to 'aug'.",
        f"{REL_PATH}:8 Converting field 'number' of entry 'dummy' to integer: 1.",
        f"{REL_PATH}:9 Converted the field 'tags' of entry 'dummy' to a list. You can consider "
        "storing it as such directly.",
        f"{REL_PATH}:10 Converted the field 'url' of entry 'dummy' to a list. You can consider "
        "storing it as such directly.",
        f"{REL_PATH}:4 The field 'ID' of entry 'dummy' is no longer required. It will be inferred "
        "from the entry label.",
    ]

    def _assert(self, out: str) -> None:
        for msg, truth in zip_longest(out.split("\n"), self.EXPECTED):
            if msg.strip() and truth:
                assert msg == truth

    def test_no_lint_warnings(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test the case of no raised lint warnings.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        cmd = LintCommand()
        cmd.execute()
        lint_messages = cmd.render_porcelain()

        for msg, exp in zip_longest(
            lint_messages, ["Congratulations! Your database triggers no lint messages."]
        ):
            if msg.strip() and exp:
                assert msg == exp

        assert (
            "cobib.database.database",
            35,
            "Encountered the following exception during cache lookup: 'Bypassing the cache.'",
        ) in caplog.record_tuples

    @pytest.mark.parametrize(
        "setup",
        [
            {
                "git": False,
                "database": True,
                "database_filename": "linting_database.yaml",
                "database_location": "commands",
            },
            {
                "git": True,
                "database": True,
                "database_filename": "linting_database.yaml",
                "database_location": "commands",
            },
        ],
        indirect=["setup"],
    )
    def test_lint_auto_format(self, setup: Any) -> None:
        """Test automatic lint formatter.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        git = setup.get("git", False)

        # apply linting with formatting and check for the expected lint messages
        cmd = LintCommand("--format")
        cmd.execute()
        pre_lint_messages = cmd.render_porcelain()
        expected_messages = [
            "The following lint messages have successfully been resolved:",
            *self.EXPECTED,
        ]
        for msg, truth in zip_longest(pre_lint_messages, expected_messages):
            if msg.strip() and truth:
                fixed = truth.replace(
                    str(TestLintDatabase.REL_PATH), str(RelPath(config.database.file))
                )
                assert msg == fixed

        # assert auto-formatted database
        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(
                get_resource("linted_database.yaml", "commands"), "r", encoding="utf-8"
            ) as expected:
                for line, truth in zip_longest(file.readlines(), expected.readlines()):
                    assert line == truth

        # assert git message
        if git:
            self.assert_git_commit_message(
                "lint",
                {
                    "format": True,
                },
            )

        # recheck linting and assert no lint messages
        cmd = LintCommand()
        cmd.execute()
        post_lint_messages = cmd.render_porcelain()
        for msg, exp in zip_longest(
            post_lint_messages, ["Congratulations! Your database triggers no lint messages."]
        ):
            if msg.strip() and exp:
                assert msg == exp
