"""Tests for coBib's ISBNParser."""
# pylint: disable=no-self-use,unused-argument

import json
import logging
from typing import Dict, Optional

import pytest
import requests

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import ISBNParser

from .parser_test import ParserTest


def assert_default_test_entry(entry: Entry) -> None:
    """Asserts that the passed entry is the default testing entry.

    Args:
        entry: the entry to assert.
    """
    assert entry.label == "Lutz2013"
    assert entry.data["author"] == "Mark Lutz"
    assert entry.data["pages"] == 1540
    assert entry.data["title"] == "Learning Python"
    assert entry.data["year"] == 2013


class TestISBNParser(ParserTest):
    """Tests for coBib's ISBNParser."""

    def test_from_isbn(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing from ISBN.

        Args:
            caplog: the built-in pytest fixture.
        """
        entries = ISBNParser().parse("978-1-449-35573-9")

        if any(
            s == "cobib.parsers.isbn" and t == logging.ERROR for s, t, _ in caplog.record_tuples
        ):
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)

    # regression test for https://gitlab.com/mrossinek/cobib/-/issues/53
    def test_from_empty_isbn(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing an empty ISBN.

        Args:
            caplog: the built-in pytest fixture.
        """
        entries = ISBNParser().parse("3860704443")

        if any(
            s == "cobib.parsers.isbn" and t == logging.ERROR for s, t, _ in caplog.record_tuples
        ):
            pytest.skip("The requests API encountered an error. Skipping test.")

        assert not entries
        assert entries == {}

        assert ("cobib.parsers.isbn", logging.WARNING) in [
            (source, level) for source, level, _ in caplog.record_tuples
        ]

    def test_catching_api_error(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test catching API error.

        Args:
            caplog: the built-in pytest fixture.
            monkeypatch: the built-in pytest fixture.
        """

        def raise_exception(*args, **kwargs):  # type: ignore
            """Mock function to raise an Exception."""
            raise requests.exceptions.RequestException()

        monkeypatch.setattr(requests, "get", raise_exception)
        ISBNParser().parse("978-1-449-35573-9")

        assert (
            "cobib.parsers.isbn",
            logging.ERROR,
            "An Exception occurred while trying to query the ISBN: 978-1-449-35573-9.",
        ) in caplog.record_tuples

    def test_catching_decode_error(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test catching json decode error.

        Args:
            caplog: the built-in pytest fixture.
            monkeypatch: the built-in pytest fixture.
        """

        def raise_exception(*args, **kwargs):  # type: ignore
            """Mock function to raise an Exception."""
            raise json.JSONDecodeError("", "", 0)

        monkeypatch.setattr(json, "loads", raise_exception)
        ISBNParser().parse("978-1-449-35573-9")

        for record in caplog.record_tuples:
            if (
                record[0] == "cobib.parsers.isbn"
                and record[1] == logging.ERROR
                and "An Exception occurred while parsing the query results:" in record[2]
            ):
                break
        else:
            pytest.fail("No Error caught by ISBNParser")

    def test_dump(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test dumping.

        Args:
            caplog: the built-in pytest fixture.
        """
        entry = Entry("dummy", {"ENTRYTYPE": "unpublished"})
        ISBNParser().dump(entry)

        assert (
            "cobib.parsers.isbn",
            logging.ERROR,
            "Cannot dump an entry as an ISBN.",
        ) in caplog.record_tuples

    def test_event_pre_isbn_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PreISBNParse event."""

        @Event.PreISBNParse.subscribe
        def hook(string: str) -> Optional[str]:
            return "978-1-449-35573-9"

        assert Event.PreISBNParse.validate()

        entries = ISBNParser().parse("Hello world!")
        if any(
            s == "cobib.parsers.isbn" and t == logging.ERROR for s, t, _ in caplog.record_tuples
        ):
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)

    def test_event_post_isbn_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PostISBNParse event."""

        @Event.PostISBNParse.subscribe
        def hook(bib: Dict[str, Entry]) -> None:
            bib["Lutz2013"].data["test"] = "dummy"

        assert Event.PostISBNParse.validate()

        entries = ISBNParser().parse("978-1-449-35573-9")
        if any(
            s == "cobib.parsers.isbn" and t == logging.ERROR for s, t, _ in caplog.record_tuples
        ):
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)
        assert entry.data["test"] == "dummy"
