"""Tests for CoBib's ArxivParser."""
# pylint: disable=no-self-use,unused-argument

import logging

from test.parsers.parser_test import ParserTest

import pytest
import requests

from cobib import parsers
from cobib.database import Entry


class TestArxivParser(ParserTest):
    """Tests for CoBib's ArxivParser."""

    def test_from_arxiv(self, caplog):
        """Test parsing from arxiv."""
        entries = parsers.ArxivParser().parse('1812.09976')

        if ('cobib.parsers.arxiv', logging.ERROR,
            'An Exception occurred while trying to query the arXiv ID: 1812.09976.') \
                in caplog.record_tuples:
            pytest.skip('The requests API encountered an error. Skipping test.')

        entry = list(entries.values())[0]
        entry.escape_special_chars()
        assert entry.label == 'Cao2018'
        assert entry.data['archivePrefix'] == 'arXiv'
        assert entry.data['arxivid'].startswith('1812.09976')
        assert entry.data['author'] == "Yudong Cao and Jonathan Romero and Jonathan P. Olson " + \
            "and Matthias Degroote and Peter D. Johnson and M{\\'a}ria Kieferov{\\'a} and Ian " + \
            "D. Kivlichan and Tim Menke and Borja Peropadre and Nicolas P. D. Sawaya and Sukin " + \
            "Sim and Libor Veis and Al{\\'a}n Aspuru-Guzik"
        assert entry.data['doi'].startswith('10.1021/acs.chemrev.8b00803')
        assert entry.data['title'] == 'Quantum Chemistry in the Age of Quantum Computing'
        assert entry.data['year'] == '2018'

    # regression test for https://gitlab.com/mrossinek/cobib/-/issues/57
    def test_invalid_arxiv_id(self):
        """Test parsing an invalid arXiv ID."""
        entries = parsers.ArxivParser().parse('10.1021/acs.chemrev.8b00803')
        assert not entries
        assert entries == {}

    def test_arxiv_without_doi(self):
        """Test parsing an arXiv ID without an associated DOI."""
        entries = parsers.ArxivParser().parse('1701.08213')
        entry = list(entries.values())[0]
        assert entry.label == 'Bravyi2017'
        assert entry.data['archivePrefix'] == 'arXiv'
        assert entry.data['arxivid'].startswith('1701.08213')
        assert entry.data['author'] == "Sergey Bravyi and Jay M. Gambetta and Antonio Mezzacapo" + \
            " and Kristan Temme"
        assert entry.data['title'] == 'Tapering off qubits to simulate fermionic Hamiltonians'
        assert entry.data['year'] == '2017'

    def test_catching_api_error(self, caplog, monkeypatch):
        """Test catching API error."""
        def raise_exception(*args, **kwargs):
            """Mock function to raise an Exception."""
            raise requests.exceptions.RequestException()

        monkeypatch.setattr(requests, 'get', raise_exception)
        parsers.ArxivParser().parse('dummy')

        assert ('cobib.parsers.arxiv', logging.ERROR,
                'An Exception occurred while trying to query the arXiv ID: dummy.') \
            in caplog.record_tuples

    def test_dump(self, caplog):
        """Test dumping."""
        entry = Entry('dummy', {'ID': 'dummy', 'ENTRYTYPE': 'unpublished'})
        parsers.ArxivParser().dump(entry)

        assert ('cobib.parsers.arxiv', logging.ERROR, 'Cannot dump an entry as an arXiv ID.') \
            in caplog.record_tuples
