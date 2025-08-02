"""Tests for coBib's UnifyLabelsCommand."""

from __future__ import annotations

from itertools import zip_longest
from typing import TYPE_CHECKING, Any, ClassVar

import pytest
from typing_extensions import override

from cobib.commands.unify_labels import UnifyLabelsCommand
from cobib.config import config
from cobib.utils.rel_path import RelPath
from tests.commands.command_test import CommandTest

from .. import get_resource

if TYPE_CHECKING:
    import cobib.commands


class TestUnifyLabels(CommandTest):
    """Tests for the shell helper which unifies all database labels."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return UnifyLabelsCommand

    REL_PATH = RelPath(get_resource("unifying_database.yaml", "commands"))

    EXPECTED: ClassVar[list[str]] = [
        "[INFO] Associated files will not be preserved.",
        "[INFO] einstein: changing field 'label' from einstein to Einstein1905_a",
        "[INFO] latexcompanion: changing field 'label' from latexcompanion to Goossens1993",
        "[INFO] knuthwebsite: changing field 'label' from knuthwebsite to Knuth",
        "[INFO] Einstein_1905: changing field 'label' from Einstein_1905 to Einstein1905_b",
        "[INFO] New and previous values match. Skipping modification of entry 'Einstein1905'.",
        "[INFO] einstein_2: changing field 'label' from einstein_2 to Einstein1905_c",
        "[INFO] New and previous values match. Skipping modification of entry 'Author2021'.",
        "[INFO] Pavošević2023: changing field 'label' from Pavošević2023 to Pavosevic2023",
    ]

    def _assert(self, out: list[str]) -> None:
        filtered = [line for line in out if line.startswith("[INFO]")]
        for msg, truth in zip_longest(filtered, self.EXPECTED):
            assert msg == truth

    @pytest.fixture
    def post_setup(self) -> None:
        """Additional setup instructions.

        Yields:
            The internally used parameters for potential later re-use during the actual test.
        """
        config.database.format.label_default = "{unidecode(author[0].last)}{year}"

    @pytest.mark.parametrize(
        "setup",
        [
            {
                "git": False,
                "database": True,
                "database_filename": "unifying_database.yaml",
                "database_location": "commands",
            },
        ],
        indirect=["setup"],
    )
    def test_dry(self, setup: Any, post_setup: Any) -> None:
        """Test the shell_helper method itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
        """
        cmd = UnifyLabelsCommand()
        cmd.execute()
        out = cmd.render_porcelain()
        self._assert(out)

    @pytest.mark.parametrize(
        "setup",
        [
            {
                "git": False,
                "database": True,
                "database_filename": "unifying_database.yaml",
                "database_location": "commands",
            },
            {
                "git": True,
                "database": True,
                "database_filename": "unifying_database.yaml",
                "database_location": "commands",
            },
        ],
        indirect=["setup"],
    )
    def test_command(self, setup: Any, post_setup: Any) -> None:
        """Test actual changes of label unification.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
        """
        git = setup.get("git", False)

        # apply label unification
        cmd = UnifyLabelsCommand("--apply")
        cmd.execute()

        # assert unified database
        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(
                RelPath(get_resource("unified_database.yaml", "commands")).path,
                "r",
                encoding="utf-8",
            ) as expected:
                for line, truth in zip_longest(file.readlines(), expected.readlines()):
                    assert line == truth

        # assert git message
        if git:
            self.assert_git_commit_message(
                "modify",
                {
                    "modification": ("label", config.database.format.label_default),
                    "dry": False,
                    "add": False,
                    "remove": False,
                    "preserve_files": None,
                    "selection": False,
                    "filter": ["++label", ""],
                },
            )
