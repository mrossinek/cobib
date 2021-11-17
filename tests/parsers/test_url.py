"""Tests for coBib's URLParser."""
# pylint: disable=no-self-use,unused-argument

import logging
from typing import Callable, Dict, Optional

import pytest

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import URLParser

from .parser_test import ParserTest
from .test_arxiv import assert_default_test_entry as assert_arxiv_entry
from .test_doi import assert_default_test_entry as assert_doi_entry


def assert_default_test_entry(entry: Entry) -> None:
    """Asserts that the passed entry is the default testing entry.

    Args:
        entry: the entry to assert.
    """
    entry.escape_special_chars()
    assert entry.label == "Grimsley_2019"
    assert entry.data["doi"] == "10.1038/s41467-019-10988-2"
    assert entry.data["url"] == ["https://doi.org/10.1038%2Fs41467-019-10988-2"]
    assert entry.data["year"] == 2019
    assert entry.data["month"] == "jul"
    assert entry.data["publisher"] == "Springer Science and Business Media {LLC}"
    assert entry.data["volume"] == 10
    assert entry.data["number"] == 1
    assert (
        entry.data["author"]
        == "Harper R. Grimsley and Sophia E. Economou and Edwin Barnes and Nicholas J. Mayhall"
    )
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
            ("https://arxiv.org/abs/1812.09976", assert_arxiv_entry),
            ("https://doi.org/10.1021/acs.chemrev.8b00803", assert_doi_entry),
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

        entry = list(entries.values())[0]
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

        entry = list(entries.values())[0]
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

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)
        assert entry.data["test"] == "dummy"
