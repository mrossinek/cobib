"""Tests for CoBib's parsing module"""

from os import path
import pytest
from cobib import parser

EXAMPLE_BIBTEX_FILE = 'test/example_entry.bib'
EXAMPLE_YAML_FILE = 'test/example_entry.yaml'

EXAMPLE_ENTRY_DICT = {
    'ENTRYTYPE': 'article',
    'ID': 'Cao_2019',
    'author': "Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and Peter"
              + " D. Johnson and M{\\'{a}}ria Kieferov{\\'{a}} and Ian D. Kivlichan and Tim Menke "
              + "and Borja Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and "
              + "Al{\\'{a}}n Aspuru-Guzik",
    'doi': '10.1021/acs.chemrev.8b00803',
    'journal': 'Chemical Reviews',
    'month': 'aug',
    'number': '19',
    'pages': '10856--10915',
    'publisher': 'American Chemical Society ({ACS})',
    'title': 'Quantum Chemistry in the Age of Quantum Computing',
    'url': 'https://doi.org/10.1021%2Facs.chemrev.8b00803',
    'volume': '119',
    'year': '2019',
}


def test_entry_set_label():
    """Test label changing"""
    # this test may fail if the input dict is not copied
    entry = parser.Entry('article', EXAMPLE_ENTRY_DICT)
    entry.set_label('Cao2019')
    assert entry.label == 'Cao2019'
    assert entry.data['ID'] == 'Cao2019'


def test_entry_set_tags():
    """Test tags setting"""
    entry = parser.Entry('article', EXAMPLE_ENTRY_DICT)
    # NB: tags must be a list
    entry.set_tags(['foo'])
    assert entry.data['tags'] == 'foo'
    # '+' signs are stripped
    entry.set_tags(['+foo'])
    assert entry.data['tags'] == 'foo'
    # also multiple occurrences
    entry.set_tags(['++foo'])
    assert entry.data['tags'] == 'foo'
    # list works as expected
    entry.set_tags(['foo', 'bar'])
    assert entry.data['tags'] == 'foo, bar'
    entry.set_tags(['+foo', 'bar'])
    assert entry.data['tags'] == 'foo, bar'
    entry.set_tags(['+foo', '+bar'])
    assert entry.data['tags'] == 'foo, bar'


def test_entry_set_file():
    """Test file setting"""
    entry = parser.Entry('article', EXAMPLE_ENTRY_DICT)
    entry.set_file(EXAMPLE_BIBTEX_FILE)
    # checks for absolute path
    assert entry.data['file'] == path.abspath(EXAMPLE_BIBTEX_FILE)


def test_entry_matches():
    """Test match filter"""
    entry = parser.Entry('article', EXAMPLE_ENTRY_DICT)
    # author must match
    _filter = {('author', True): ['Cao']}
    assert entry.matches(_filter, _or=False)
    # author must NOT match
    _filter = {('author', False): ['Coa']}
    assert entry.matches(_filter, _or=False)
    # author and year must match
    _filter = {('author', True): ['Cao'], ('year', True): ['2019']}
    assert entry.matches(_filter, _or=False)
    # author OR year must match
    _filter = {('author', True): ['Cao'], ('year', True): ['2020']}
    assert entry.matches(_filter, _or=True)
    _filter = {('author', True): ['Coa'], ('year', True): ['2019']}
    assert entry.matches(_filter, _or=True)
    # author must NOT match but year must match
    _filter = {('author', False): ['Coa'], ('year', True): ['2019']}
    assert entry.matches(_filter, _or=False)


def test_to_bibtex():
    """Test to bibtex conversion"""
    pytest.skip("Testing this string is too ambigious. Assumed to be tested by bibtexparser.")


def test_to_yaml():
    """Test to yaml conversion"""
    entry = parser.Entry('article', EXAMPLE_ENTRY_DICT)
    yaml_str = entry.to_yaml()
    with open(EXAMPLE_YAML_FILE, 'r') as file:
        assert yaml_str == file.read()


def test_parser_from_bibtex_as_string():
    """Test parsing a bibtex string"""
    with open(EXAMPLE_BIBTEX_FILE, 'r') as file:
        bibtex_str = file.read()
    entries = parser.Entry.from_bibtex(bibtex_str, string=True)
    entry = list(entries.values())[0]
    assert entry.data == EXAMPLE_ENTRY_DICT


def test_parser_from_bibtex_as_file():
    """Test parsing a bibtex file"""
    with open(EXAMPLE_BIBTEX_FILE, 'r') as bibtex_file:
        entries = parser.Entry.from_bibtex(bibtex_file, string=False)
        entry = list(entries.values())[0]
        assert entry.data == EXAMPLE_ENTRY_DICT


def test_parser_from_yaml_as_file():
    """Test parsing a yaml file"""
    with open(EXAMPLE_YAML_FILE, 'r') as yaml_file:
        entries = parser.Entry.from_yaml(yaml_file)
        entry = list(entries.values())[0]
        assert entry.data == EXAMPLE_ENTRY_DICT


def test_parser_from_doi():
    """Test parsing from doi"""
    entries = parser.Entry.from_doi('10.1021/acs.chemrev.8b00803')
    entry = list(entries.values())[0]
    assert entry.data == EXAMPLE_ENTRY_DICT


def test_parser_from_arxiv():
    """Test parsing from arxiv"""
    entries = parser.Entry.from_arxiv('1812.09976')
    entry = list(entries.values())[0]
    # cannot assert against EXAMPLE_ENTRY_DICT due to outdated reference on arxiv
    # thus, we simply assert that the data dictionary is not empty
    assert entry.data
