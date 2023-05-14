"""Tests for coBib's ZoteroImporter."""
# pylint: disable=unused-argument

import json
import logging
import tempfile
from itertools import zip_longest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    def _get_authentication_tokens(no_cache: bool = False) -> Dict[str, str]:
        return {
            # NOTE: we are relying on the publicly accessible user `cobib` for testing purposes
            "UserID": "8608002",
        }


class TestZoteroImporter(ImporterTest):
    """Tests for coBib's ZoteroImporter."""

    def _assert_results(self, imported_entries: List[Entry]) -> None:
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

    def test_fetch(self) -> None:
        """Test fetching entries from the Zotero API."""
        importer = MockZoteroImporter()
        # NOTE: even though attachments are not accessible via public libraries, we explicitly skip
        # downloading them, just to be sure.
        imported_entries = importer.fetch(skip_download=False)

        self._assert_results(imported_entries)

    def test_fetch_custom_user_id(self) -> None:
        """Test fetching with custom user ID."""
        imported_entries = ZoteroImporter().fetch("--user-id", "8608002", "--no-cache")
        self._assert_results(imported_entries)

    def test_cache(self) -> None:
        """Test caching behavior."""
        try:
            config.logging.cache = str(Path(tempfile.gettempdir()) / "cache")
            imported_entries = ZoteroImporter().fetch("--user-id", "8608002", skip_download=True)
            self._assert_results(imported_entries)

            with open(config.logging.cache, "r", encoding="utf-8") as cache:
                cached_data = json.load(cache)
                assert "Zotero" in cached_data.keys()
                assert "UserID" in cached_data["Zotero"].keys()
                assert cached_data["Zotero"]["UserID"] == "8608002"
        finally:
            config.defaults()

    def test_handle_argument_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of ArgumentError.

        Args:
            caplog: the built-in pytest fixture.
        """
        ZoteroImporter().fetch("--dummy")
        for source, level, message in caplog.record_tuples:
            if ("cobib.importers.zotero", logging.ERROR) == (
                source,
                level,
            ) and "Error: zotero: error:" in message:
                break
        else:
            pytest.fail("No Error logged from ArgumentParser.")

    def test_event_pre_zotero_import(self) -> None:
        """Tests the PreZoteroImport event."""

        @Event.PreZoteroImport.subscribe
        def hook(
            protected_url: str, authentication: Dict[str, str]
        ) -> Optional[Tuple[str, Dict[str, str]]]:
            return (protected_url.replace("test", "8608002"), {})

        assert Event.PreZoteroImport.validate()

        imported_entries = ZoteroImporter().fetch("--user-id", "test", "--no-cache")

        self._assert_results(imported_entries)

    def test_event_post_zotero_import(self) -> None:
        """Tests the PostZoteroImport event."""

        @Event.PostZoteroImport.subscribe
        def hook(imported_entries: List[Entry]) -> Optional[List[Entry]]:
            return []

        assert Event.PostZoteroImport.validate()

        imported_entries = MockZoteroImporter().fetch("--no-cache")
        assert imported_entries == []
