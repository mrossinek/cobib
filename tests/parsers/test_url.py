"""Tests for coBib's URLParser."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Dict, Optional

import pytest

from cobib.config import Event
from cobib.database import Author, Entry
from cobib.parsers import URLParser

from .parser_test import ParserTest
from .test_arxiv import assert_default_test_entry as assert_arxiv_entry
from .test_doi import assert_default_test_entry as assert_doi_entry
from .test_isbn import assert_default_test_entry as assert_isbn_entry


def assert_default_test_entry(entry: Entry) -> None:
    """Asserts that the passed entry is the default testing entry.

    Args:
        entry: the entry to assert.
    """
    assert entry.label == "Grimsley_2019"
    assert entry.data["doi"] == "10.1038/s41467-019-10988-2"
    assert entry.data["url"] == ["http://dx.doi.org/10.1038/s41467-019-10988-2"]
    assert entry.data["year"] == 2019
    assert entry.data["month"] == "jul"
    assert entry.data["publisher"] == "Springer Science and Business Media LLC"
    assert entry.data["volume"] == 10
    assert entry.data["number"] == 1
    assert entry.data["author"] == [
        Author("Harper R.", "Grimsley"),
        Author("Sophia E.", "Economou"),
        Author("Edwin", "Barnes"),
        Author("Nicholas J.", "Mayhall"),
    ]
    assert (
        entry.data["title"]
        == "An adaptive variational algorithm for exact molecular simulations on a quantum computer"
    )
    assert entry.data["journal"] == "Nature Communications"


class TestURLParser(ParserTest):
    """Tests for coBib's URLParser."""

    @pytest.mark.parametrize(
        ("query", "assertion"),
        [
            ("978-1-449-35573-9", assert_isbn_entry),
            ("https://arxiv.org/abs/1701.08213", assert_arxiv_entry),
            ("https://doi.org/10.1021/acs.jpclett.3c00330", assert_doi_entry),
            ("https://www.nature.com/articles/s41467-019-10988-2", assert_default_test_entry),
        ],
    )
    def test_from_url(
        self, query: str, assertion: Callable[[Entry], None], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test parsing from URL.

        Args:
            query: the URL which to query.
            assertion: the assertion method to run.
            caplog: the built-in pytest fixture.
        """
        entries = URLParser().parse(query)

        try:
            entry = next(iter(entries.values()))
        except (IndexError, StopIteration):
            pytest.skip("Skipping because we likely ran into a network timeout.")

        assertion(entry)

    def test_invalid_url(self) -> None:
        """Test parsing an invalid URL."""
        entries = URLParser().parse("https://github.com/")
        assert not entries
        assert entries == {}

    def test_dump(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test dumping.

        Args:
            caplog: the built-in pytest fixture.
        """
        entry = Entry("dummy", {"ENTRYTYPE": "unpublished"})
        URLParser().dump(entry)

        assert (
            "cobib.parsers.url",
            logging.ERROR,
            "Cannot dump an entry as a URL.",
        ) in caplog.record_tuples

    def test_event_pre_url_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PreURLParse event."""

        @Event.PreURLParse.subscribe
        def hook(string: str) -> Optional[str]:
            return "https://www.nature.com/articles/s41467-019-10988-2"

        assert Event.PreURLParse.validate()

        entries = URLParser().parse("Hello world!")
        if any(s == "cobib.parsers.url" and t == logging.ERROR for s, t, _ in caplog.record_tuples):
            pytest.skip("The requests API encountered an error. Skipping test.")

        try:
            entry = next(iter(entries.values()))
        except (IndexError, StopIteration):
            pytest.skip("Skipping because we likely ran into a network timeout.")
        assert_default_test_entry(entry)

    def test_event_post_url_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PostURLParse event."""

        @Event.PostURLParse.subscribe
        def hook(bib: Dict[str, Entry]) -> None:
            bib["Grimsley_2019"].data["test"] = "dummy"

        assert Event.PostURLParse.validate()

        entries = URLParser().parse("https://www.nature.com/articles/s41467-019-10988-2")
        if any(s == "cobib.parsers.url" and t == logging.ERROR for s, t, _ in caplog.record_tuples):
            pytest.skip("The requests API encountered an error. Skipping test.")

        try:
            entry = next(iter(entries.values()))
        except (IndexError, StopIteration):
            pytest.skip("Skipping because we likely ran into a network timeout.")
        assert_default_test_entry(entry)
        assert entry.data["test"] == "dummy"
