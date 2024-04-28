"""Tests for coBib's ZoteroImporter."""

from __future__ import annotations

import json
import tempfile
from itertools import zip_longest
from pathlib import Path

import pytest
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Entry
from cobib.importers import ZoteroImporter
from cobib.parsers import YAMLParser

from .. import get_resource
from .importer_test import ImporterTest

EXPECTED_DATABASE = get_resource("zotero_database.yaml", "importers")


class MockZoteroImporter(ZoteroImporter):
    """This class mocks the `ZoteroImporter` by providing fake OAuth authentication tokens."""

    @override
    @staticmethod
    def _get_authentication_tokens(no_cache: bool = False) -> dict[str, str]:
        return {
            # NOTE: we are relying on the publicly accessible user `cobib` for testing purposes
            "UserID": "8608002",
        }


class TestZoteroImporter(ImporterTest):
    """Tests for coBib's ZoteroImporter."""

    def _assert_results(self, imported_entries: list[Entry]) -> None:
        """Common assertion utility method.

        Args:
            imported_entries: the list of entries to assert against the expected database.
        """
        parser = YAMLParser()

        imported_database = ""
        for entry in imported_entries:
            entry_str = parser.dump(entry)
            if entry_str is not None:
                imported_database += entry_str

        with open(EXPECTED_DATABASE, "r", encoding="utf-8") as expected:
            for line, truth in zip_longest(
                imported_database.splitlines(keepends=True), expected.readlines()
            ):
                assert line == truth

    @pytest.mark.asyncio
    async def test_fetch(self) -> None:
        """Test fetching entries from the Zotero API."""
        importer = MockZoteroImporter(skip_download=True)
        # NOTE: even though attachments are not accessible via public libraries, we explicitly skip
        # downloading them, just to be sure.
        imported_entries = await importer.fetch()

        self._assert_results(imported_entries)

    @pytest.mark.asyncio
    async def test_fetch_custom_user_id(self) -> None:
        """Test fetching with custom user ID."""
        imported_entries = await ZoteroImporter("--user-id", "8608002", "--no-cache").fetch()
        self._assert_results(imported_entries)

    @pytest.mark.asyncio
    async def test_cache(self) -> None:
        """Test caching behavior."""
        try:
            config.logging.cache = str(Path(tempfile.gettempdir()) / "cache")
            imported_entries = await ZoteroImporter(
                "--user-id", "8608002", skip_download=True
            ).fetch()
            self._assert_results(imported_entries)

            with open(config.logging.cache, "r", encoding="utf-8") as cache:
                cached_data = json.load(cache)
                assert "Zotero" in cached_data.keys()
                assert "UserID" in cached_data["Zotero"].keys()
                assert cached_data["Zotero"]["UserID"] == "8608002"
        finally:
            config.defaults()

    @pytest.mark.asyncio
    async def test_event_pre_zotero_import(self) -> None:
        """Tests the PreZoteroImport event."""

        @Event.PreZoteroImport.subscribe
        def hook(importer: ZoteroImporter) -> None:
            importer.protected_url = importer.protected_url.replace("test", "8608002")

        assert Event.PreZoteroImport.validate()

        imported_entries = await ZoteroImporter("--user-id", "test", "--no-cache").fetch()

        self._assert_results(imported_entries)

    @pytest.mark.asyncio
    async def test_event_post_zotero_import(self) -> None:
        """Tests the PostZoteroImport event."""

        @Event.PostZoteroImport.subscribe
        def hook(importer: ZoteroImporter) -> None:
            importer.imported_entries = []

        assert Event.PostZoteroImport.validate()

        imported_entries = await MockZoteroImporter("--no-cache").fetch()
        assert imported_entries == []
