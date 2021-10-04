"""Tests for coBib's ArxivParser."""
# pylint: disable=no-self-use,unused-argument

import logging
from typing import Dict, Optional

import pytest
import requests

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import ArxivParser

from .parser_test import ParserTest


def assert_default_test_entry(entry: Entry) -> None:
    """Asserts that the passed entry is the default testing entry.

    Args:
        entry: the entry to assert.
    """
    entry.escape_special_chars()
    assert entry.label == "Cao2018"
    assert entry.data["archivePrefix"] == "arXiv"
    assert entry.data["arxivid"].startswith("1812.09976")
    assert (
        entry.data["author"]
        == "Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and "
        + "Peter D. Johnson and M{\\'a}ria Kieferov{\\'a} and Ian D. Kivlichan and Tim Menke "
        + "and Borja Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and "
        + "Al{\\'a}n Aspuru-Guzik"
    )
    assert entry.data["doi"].startswith("10.1021/acs.chemrev.8b00803")
    assert entry.data["title"] == "Quantum Chemistry in the Age of Quantum Computing"
    assert entry.data["year"] == 2018
    assert entry.data["_download"] == "http://arxiv.org/pdf/1812.09976v2"


class TestArxivParser(ParserTest):
    """Tests for coBib's ArxivParser."""

    @pytest.mark.parametrize("query", ["1812.09976", "https://arxiv.org/abs/1812.09976"])
    def test_from_arxiv(self, query: str, caplog: pytest.LogCaptureFixture) -> None:
        """Test parsing from arXiv.

        Args:
            query: the arXiv ID or URL which to query.
            caplog: the built-in pytest fixture.
        """
        entries = ArxivParser().parse(query)

        if (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "An Exception occurred while trying to query the arXiv ID: 1812.09976.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)

    # regression test for https://gitlab.com/mrossinek/cobib/-/issues/57
    def test_invalid_arxiv_id(self) -> None:
        """Test parsing an invalid arXiv ID."""
        entries = ArxivParser().parse("10.1021/acs.chemrev.8b00803")
        assert not entries
        assert entries == {}

    def test_arxiv_without_doi(self) -> None:
        """Test parsing an arXiv ID without an associated DOI."""
        entries = ArxivParser().parse("1701.08213")
        entry = list(entries.values())[0]
        assert entry.label == "Bravyi2017"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["arxivid"].startswith("1701.08213")
        assert (
            entry.data["author"]
            == "Sergey Bravyi and Jay M. Gambetta and Antonio Mezzacapo and Kristan Temme"
        )
        assert entry.data["title"] == "Tapering off qubits to simulate fermionic Hamiltonians"
        assert entry.data["year"] == 2017

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
        ArxivParser().parse("1812.0997")

        assert (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "An Exception occurred while trying to query the arXiv ID: 1812.0997.",
        ) in caplog.record_tuples

    def test_dump(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test dumping.

        Args:
            caplog: the built-in pytest fixture.
        """
        entry = Entry("dummy", {"ENTRYTYPE": "unpublished"})
        ArxivParser().dump(entry)

        assert (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "Cannot dump an entry as an arXiv ID.",
        ) in caplog.record_tuples

    def test_event_pre_arxiv_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PreArxivParse event."""

        @Event.PreArxivParse.subscribe
        def hook(string: str) -> Optional[str]:
            return "1812.09976"

        assert Event.PreArxivParse.validate()

        entries = ArxivParser().parse("Hello world!")
        if (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "An Exception occurred while trying to query the arXiv ID: 1812.09976.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)

    def test_event_post_arxiv_parse(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests the PostArxivParse event."""

        @Event.PostArxivParse.subscribe
        def hook(bib: Dict[str, Entry]) -> None:
            bib["Cao2018"].data["test"] = "dummy"

        assert Event.PostArxivParse.validate()

        entries = ArxivParser().parse("1812.09976")
        if (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "An Exception occurred while trying to query the arXiv ID: 1812.09976.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        entry = list(entries.values())[0]
        assert_default_test_entry(entry)
        assert entry.data["test"] == "dummy"
