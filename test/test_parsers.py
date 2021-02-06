"""Tests for CoBib's parsing module."""

from os import path
from pathlib import Path
import pytest
from cobib import parsers
from cobib.config import config
from cobib.database import Entry

EXAMPLE_BIBTEX_FILE = 'test/example_entry.bib'
EXAMPLE_YAML_FILE = 'test/example_entry.yaml'

EXAMPLE_ENTRY_DICT = {
    'ENTRYTYPE': 'article',
    'ID': 'Cao_2019',
    'author': "Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and Peter"
              + " D. Johnson and M{\\'a}ria Kieferov{\\'a} and Ian D. Kivlichan and Tim Menke "
              + "and Borja Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and "
              + "Al{\\'a}n Aspuru-Guzik",
    'doi': '10.1021/acs.chemrev.8b00803',
    'journal': 'Chemical Reviews',
    'month': '8',
    'number': '19',
    'pages': '10856--10915',
    'publisher': 'American Chemical Society ({ACS})',
    'title': 'Quantum Chemistry in the Age of Quantum Computing',
    'url': 'https://doi.org/10.1021%2Facs.chemrev.8b00803',
    'volume': '119',
    'year': '2019',
}


def test_to_bibtex():
    """Test to bibtex conversion."""
    pytest.skip("Testing this string is too ambigious. Assumed to be tested by bibtexparser.")


def test_to_yaml():
    """Test to yaml conversion."""
    # ensure the config is set to its defaults
    config.defaults()
    entry = Entry(EXAMPLE_ENTRY_DICT['ID'], EXAMPLE_ENTRY_DICT)
    yaml_str = parsers.YAMLParser().dump(entry)
    with open(EXAMPLE_YAML_FILE, 'r') as file:
        assert yaml_str == file.read()


@pytest.mark.parametrize('month_type', [int, str])
def test_parser_from_bibtex_as_str(month_type):
    """Test parsing a bibtex string.

    Args:
        month_type (str): type to use for storing the 'month' field.
    """
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    config.database.format.month = month_type
    reference = EXAMPLE_ENTRY_DICT.copy()
    if month_type == str:
        reference['month'] = 'aug'
    with open(EXAMPLE_BIBTEX_FILE, 'r') as file:
        bibtex_str = file.read()
    entries = parsers.BibtexParser().parse(bibtex_str)
    entry = list(entries.values())[0]
    entry.convert_month(month_type)
    assert entry.data == reference


@pytest.mark.parametrize('month_type', [int, str])
def test_parser_from_bibtex_as_file(month_type):
    """Test parsing a bibtex file.

    Args:
        month_type (str): type to use for storing the 'month' field.
    """
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    config.database.format.month = month_type
    reference = EXAMPLE_ENTRY_DICT.copy()
    if month_type == str:
        reference['month'] = 'aug'
    entries = parsers.BibtexParser().parse(EXAMPLE_BIBTEX_FILE)
    entry = list(entries.values())[0]
    entry.convert_month(month_type)
    assert entry.data == reference


@pytest.mark.parametrize('month_type', [int, str])
def test_parser_from_yaml_as_file(month_type):
    """Test parsing a yaml file.

    Args:
        month_type (str): type to use for storing the 'month' field.
    """
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    config.database.format.month = month_type
    reference = EXAMPLE_ENTRY_DICT.copy()
    if month_type == str:
        reference['month'] = 'aug'
    # with open(EXAMPLE_YAML_FILE, 'r') as yaml_file:
    entries = parsers.YAMLParser().parse(EXAMPLE_YAML_FILE)
    entry = list(entries.values())[0]
    entry.convert_month(month_type)
    assert entry.data == reference


@pytest.mark.parametrize('month_type', [int, str])
def test_parser_from_doi(month_type):
    """Test parsing from doi.

    Args:
        month_type (str): type to use for storing the 'month' field.
    """
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    config.database.format.month = month_type
    reference = EXAMPLE_ENTRY_DICT.copy()
    if month_type == str:
        reference['month'] = 'aug'
    # In this specific case the bib file provided by this DOI includes additional (yet unnecessary)
    # brackets in the escaped special characters of the author field. Thus, we correct for this
    # inconsistency manually before asserting the equality.
    reference['author'] = reference['author'].replace("'a", "'{a}")
    entries = parsers.DOIParser().parse('10.1021/acs.chemrev.8b00803')
    if entries == {}:
        pytest.skip("The requests library experienced an Error!")
    entry = list(entries.values())[0]
    entry.convert_month(month_type)
    assert entry.data == reference


def test_parser_from_doi_invalid():
    """Test parsing an invalid DOI."""
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    entries = parsers.DOIParser().parse('1812.09976')
    assert not entries
    assert entries == {}


def test_parser_from_isbn():
    """Test parsing from ISBN."""
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    entries = parsers.ISBNParser().parse('978-1-449-35573-9')
    if entries == {}:
        pytest.skip("The requests library experienced an Error!")
    entry = list(entries.values())[0]
    assert entry.label == 'Lutz2013'
    assert entry.data['author'] == 'Mark Lutz'
    assert entry.data['pages'] == '1540'
    assert entry.data['title'] == 'Learning Python'
    assert entry.data['year'] == '2013'


# regression test for https://gitlab.com/mrossinek/cobib/-/issues/53
def test_parser_from_isbn_empty():
    """Test parsing an empty ISBN."""
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    entries = parsers.ISBNParser().parse('3860704443')
    assert not entries
    assert entries == {}


def test_parser_from_arxiv():
    """Test parsing from arxiv."""
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    reference = EXAMPLE_ENTRY_DICT.copy()
    entries = parsers.ArxivParser().parse('1812.09976')
    if entries == {}:
        pytest.skip("The requests library experienced an Error!")
    entry = list(entries.values())[0]
    entry.escape_special_chars()
    assert entry.label == 'Cao2018'
    assert entry.data['archivePrefix'] == 'arXiv'
    assert entry.data['arxivid'].startswith('1812.09976')
    assert entry.data['author'] == reference['author']
    assert entry.data['title'] == reference['title']
    assert entry.data['year'] == '2018'


# regression test for https://gitlab.com/mrossinek/cobib/-/issues/57
def test_parser_from_arxiv_invalid():
    """Test parsing an invalid arXiv ID."""
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    entries = parsers.ArxivParser().parse('10.1021/acs.chemrev.8b00803')
    assert not entries
    assert entries == {}
