"""Tests for coBib's DOIParser."""
# pylint: disable=no-self-use,unused-argument

import logging

import pytest
import requests

from cobib import parsers
from cobib.database import Entry

from .parser_test import ParserTest


class TestDOIParser(ParserTest):
    """Tests for coBib's DOIParser."""

    def test_from_doi(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing from DOI.

        Args:
            caplog: the built-in pytest fixture.
        """
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        # In this specific case the bib file provided by this DOI includes additional (yet
        # unnecessary) brackets in the escaped special characters of the author field. Thus, we
        # correct for this inconsistency manually before asserting the equality.
        reference["author"] = str(reference["author"]).replace("'a", "'{a}")
        reference["_download"] = "https://pubs.acs.org/doi/10.1021/acs.chemrev.8b00803"
        entries = parsers.DOIParser().parse("10.1021/acs.chemrev.8b00803")

        if (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.chemrev.8b00803.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert entry.data == reference

    def test_invalid_doi(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing an invalid DOI.

        Args:
            caplog: the built-in pytest fixture.
        """
        entries = parsers.DOIParser().parse("1812.09976")
        assert not entries
        assert entries == {}

        assert (
            "cobib.parsers.doi",
            logging.WARNING,
            "'1812.09976' is not a valid DOI.",
        ) in caplog.record_tuples

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
        parsers.DOIParser().parse("10.1021/acs.chemrev.8b00803")

        assert (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.chemrev.8b00803.",
        ) in caplog.record_tuples

    def test_dump(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test dumping.

        Args:
            caplog: the built-in pytest fixture.
        """
        entry = Entry("dummy", {"ENTRYTYPE": "unpublished"})
        parsers.DOIParser().dump(entry)

        assert (
            "cobib.parsers.doi",
            logging.ERROR,
            "Cannot dump an entry as a DOI.",
        ) in caplog.record_tuples
