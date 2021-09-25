"""Tests for coBib's URLParser."""
# pylint: disable=no-self-use,unused-argument

import logging
from typing import Callable

import pytest

from cobib import parsers
from cobib.database import Entry

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
        """Test parsing from arXiv.

        Args:
            query: the URL which to query.
            assertion: the assertion method to run.
            caplog: the built-in pytest fixture.
        """
        entries = parsers.URLParser().parse(query)

        entry = list(entries.values())[0]
        assertion(entry)

    def test_invalid_url(self) -> None:
        """Test parsing an invalid URL."""
        entries = parsers.URLParser().parse("https://github.com/")
        assert not entries
        assert entries == {}

    def test_dump(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test dumping.

        Args:
            caplog: the built-in pytest fixture.
        """
        entry = Entry("dummy", {"ENTRYTYPE": "unpublished"})
        parsers.URLParser().dump(entry)

        assert (
            "cobib.parsers.url",
            logging.ERROR,
            "Cannot dump an entry as a URL.",
        ) in caplog.record_tuples
