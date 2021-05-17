"""Tests for coBib's ISBNParser."""
# pylint: disable=no-self-use,unused-argument

import json
import logging

import pytest
import requests

from cobib import parsers
from cobib.database import Entry

from .parser_test import ParserTest


class TestISBNParser(ParserTest):
    """Tests for coBib's ISBNParser."""

    def test_from_isbn(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing from ISBN."""
        entries = parsers.ISBNParser().parse("978-1-449-35573-9")

        if any(
            s == "cobib.parsers.isbn" and t == logging.ERROR for s, t, _ in caplog.record_tuples
        ):
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert entry.label == "Lutz2013"
        assert entry.data["author"] == "Mark Lutz"
        assert entry.data["pages"] == 1540
        assert entry.data["title"] == "Learning Python"
        assert entry.data["year"] == 2013

    # regression test for https://gitlab.com/mrossinek/cobib/-/issues/53
    def test_from_empty_isbn(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing an empty ISBN."""
        entries = parsers.ISBNParser().parse("3860704443")
        assert not entries
        assert entries == {}

        assert ("cobib.parsers.isbn", logging.WARNING) in [
            (source, level) for source, level, _ in caplog.record_tuples
        ]

    def test_catching_api_error(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test catching API error."""

        def raise_exception(*args, **kwargs):  # type: ignore
            """Mock function to raise an Exception."""
            raise requests.exceptions.RequestException()

        monkeypatch.setattr(requests, "get", raise_exception)
        parsers.ISBNParser().parse("978-1-449-35573-9")

        assert (
            "cobib.parsers.isbn",
            logging.ERROR,
            "An Exception occurred while trying to query the ISBN: 978-1-449-35573-9.",
        ) in caplog.record_tuples

    def test_catching_decode_error(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test catching json decode error."""

        def raise_exception(*args, **kwargs):  # type: ignore
            """Mock function to raise an Exception."""
            raise json.JSONDecodeError("", "", 0)

        monkeypatch.setattr(json, "loads", raise_exception)
        parsers.ISBNParser().parse("978-1-449-35573-9")

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
        """Test dumping."""
        entry = Entry("dummy", {"ID": "dummy", "ENTRYTYPE": "unpublished"})
        parsers.ISBNParser().dump(entry)

        assert (
            "cobib.parsers.isbn",
            logging.ERROR,
            "Cannot dump an entry as an ISBN.",
        ) in caplog.record_tuples
