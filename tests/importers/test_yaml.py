"""Tests for coBib's YAMLImporter."""

from __future__ import annotations

from itertools import zip_longest
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ImportCommand
from cobib.config import Event
from cobib.database import Entry
from cobib.importers import YAMLImporter
from cobib.parsers import YAMLParser

from .. import get_resource
from ..commands import CommandTest
from .importer_test import ImporterTest

if TYPE_CHECKING:
    import cobib.commands

IMPORT_DATABASE = get_resource("example_literature.yaml")
EXPECTED_DATABASE = get_resource("example_literature.yaml")


class TestYAMLImporter(ImporterTest):
    """Tests for coBib's YAMLImporter."""

    @staticmethod
    def _assert_results(imported_entries: list[Entry]) -> None:
        """Common assertion utility method.

        Args:
            imported_entries: the list of entries to assert against the expected database.
        """
        parser = YAMLParser()

        imported_database = ""
        for entry in imported_entries:
            entry_str = parser.dump(entry.formatted())
            if entry_str is not None:
                imported_database += entry_str

        with open(EXPECTED_DATABASE, "r", encoding="utf-8") as expected:
            for line, truth in zip_longest(
                imported_database.splitlines(keepends=True), expected.readlines()
            ):
                assert line == truth

    @pytest.mark.asyncio
    async def test_fetch(self) -> None:
        """Test fetching entries from a YAML file."""
        importer = YAMLImporter(IMPORT_DATABASE)
        # NOTE: even though attachments are not accessible via public libraries, we explicitly skip
        # downloading them, just to be sure.
        imported_entries = await importer.fetch()

        self._assert_results(imported_entries)

    @pytest.mark.asyncio
    async def test_event_pre_yaml_import(self) -> None:
        """Tests the PreYAMLImport event."""

        @Event.PreYAMLImport.subscribe
        def hook(importer: YAMLImporter) -> None:
            importer.largs.file = IMPORT_DATABASE

        assert Event.PreYAMLImport.validate()

        imported_entries = await YAMLImporter("dummy/path.bib").fetch()

        self._assert_results(imported_entries)

    @pytest.mark.asyncio
    async def test_event_post_yaml_import(self) -> None:
        """Tests the PostYAMLImport event."""

        @Event.PostYAMLImport.subscribe
        def hook(importer: YAMLImporter) -> None:
            importer.imported_entries = []

        assert Event.PostYAMLImport.validate()

        imported_entries = await YAMLImporter(IMPORT_DATABASE).fetch()
        assert imported_entries == []


class TestYAMLImport(CommandTest):
    """Tests for coBib's YAMLImporter via the ImportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ImportCommand

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"database_filename": None, "git": False}],
            [{"database_filename": None, "git": True}],
        ],
        indirect=["setup"],
    )
    async def test_command(self, setup: Any) -> None:
        """Test importing from YAML via the ImportCommand."""
        parser_args = [IMPORT_DATABASE]
        cmd = ImportCommand("--skip-download", "--yaml", "--", *parser_args)
        await cmd.execute()

        TestYAMLImporter._assert_results(list(cmd.new_entries.values()))

        if setup.get("git", False):
            self.assert_git_commit_message(
                "import",
                {
                    "skip_download": True,
                    "importer_arguments": parser_args,
                    "bibtex": False,
                    "yaml": True,
                },
            )
