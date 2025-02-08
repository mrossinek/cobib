"""Tests for coBib's DOIParser."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import pytest
import requests

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import DOIParser

from .parser_test import ParserTest


def assert_default_test_entry(entry: Entry) -> None:
    """Asserts that the passed entry is the default testing entry.

    Args:
        entry: the entry to assert.
    """
    reference = ParserTest.EXAMPLE_ENTRY_DICT.copy()
    reference["_download"] = "https://pubs.acs.org/doi/10.1021/acs.jpclett.3c00330"
    for key in entry.data.keys():
        a = entry.data[key]
        b = reference[key]
        if a != b:
            print(key, a, b)
    assert entry.data == reference


class TestDOIParser(ParserTest):
    """Tests for coBib's DOIParser."""

    @pytest.mark.parametrize(
        "query", ["10.1021/acs.jpclett.3c00330", "https://doi.org/10.1021/acs.jpclett.3c00330"]
    )
    def test_from_doi(self, query: str, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing from DOI.

        Args:
            query: the DOI or URL which to query.
            caplog: the built-in pytest fixture.
        """
        entries = DOIParser().parse(query)

        if (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.jpclett.3c00330.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        try:
            entry = next(iter(entries.values()))
        except (IndexError, StopIteration):
            pytest.skip("Skipping because we likely ran into a network timeout.")
        assert_default_test_entry(entry)

    def test_invalid_doi(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing an invalid DOI.

        Args:
            caplog: the built-in pytest fixture.
        """
        entries = DOIParser().parse("1701.08213")
        assert not entries
        assert entries == {}

        assert (
            "cobib.parsers.doi",
            logging.WARNING,
            "'1701.08213' is not a valid DOI.",
        ) in caplog.record_tuples

    def test_catching_api_error(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test catching API error.

        Args:
            caplog: the built-in pytest fixture.
            monkeypatch: the built-in pytest fixture.
        """

        def raise_exception(*args, **kwargs):  # type: ignore[no-untyped-def]
            """Mock function to raise an Exception."""
            raise requests.exceptions.RequestException()

        monkeypatch.setattr(requests.Session, "get", raise_exception)
        DOIParser().parse("10.1021/acs.jpclett.3c00330")

        assert (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.jpclett.3c00330.",
        ) in caplog.record_tuples

    def test_dump(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test dumping.

        Args:
            caplog: the built-in pytest fixture.
        """
        entry = Entry("dummy", {"ENTRYTYPE": "unpublished"})
        DOIParser().dump(entry)

        assert (
            "cobib.parsers.doi",
            logging.ERROR,
            "Cannot dump an entry as a DOI.",
        ) in caplog.record_tuples

    def test_event_pre_doi_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PreDOIParse event."""

        @Event.PreDOIParse.subscribe
        def hook(string: str) -> Optional[str]:
            return "10.1021/acs.jpclett.3c00330"

        assert Event.PreDOIParse.validate()

        entries = DOIParser().parse("Hello world!")
        if (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.jpclett.3c00330.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        try:
            entry = next(iter(entries.values()))
        except (IndexError, StopIteration):
            pytest.skip("Skipping because we likely ran into a network timeout.")
        assert_default_test_entry(entry)

    def test_event_post_doi_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PostDOIParse event."""

        @Event.PostDOIParse.subscribe
        def hook(bib: Dict[str, Entry]) -> None:
            bib["Rossmannek_2023"].data["test"] = "dummy"

        assert Event.PostDOIParse.validate()

        entries = DOIParser().parse("10.1021/acs.jpclett.3c00330")
        if (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.jpclett.3c00330.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        try:
            entry = next(iter(entries.values()))
        except (IndexError, StopIteration):
            pytest.skip("Skipping because we likely ran into a network timeout.")
        assert entry.data["test"] == "dummy"
