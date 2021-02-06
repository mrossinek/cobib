"""Tests for CoBib's parsing module."""

from os import path
from pathlib import Path
import pytest
from cobib.config import config
from cobib.database import Database, Entry
from cobib.parsers import BibtexParser

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


def test_entry_set_label():
    """Test label changing."""
    # this test may fail if the input dict is not copied
    entry = Entry('article', EXAMPLE_ENTRY_DICT)
    entry.set_label = 'Cao2019'
    assert entry.label == 'Cao2019'
    assert entry.data['ID'] == 'Cao2019'


def test_entry_set_tags():
    """Test tags setting."""
    entry = Entry('article', EXAMPLE_ENTRY_DICT)
    # NB: tags must be a list
    entry.set_tags = ['foo']
    assert entry.data['tags'] == 'foo'
    # '+' signs are stripped
    entry.set_tags = ['+foo']
    assert entry.data['tags'] == 'foo'
    # also multiple occurrences
    entry.set_tags = ['++foo']
    assert entry.data['tags'] == 'foo'
    # list works as expected
    entry.set_tags = ['foo', 'bar']
    assert entry.data['tags'] == 'foo, bar'
    entry.set_tags = ['+foo', 'bar']
    assert entry.data['tags'] == 'foo, bar'
    entry.set_tags = ['+foo', '+bar']
    assert entry.data['tags'] == 'foo, bar'


def test_entry_set_file():
    """Test file setting."""
    entry = Entry('article', EXAMPLE_ENTRY_DICT)
    entry.set_file = EXAMPLE_BIBTEX_FILE
    # checks for absolute path
    assert entry.data['file'] == path.abspath(EXAMPLE_BIBTEX_FILE)


def test_entry_matches():
    """Test match filter."""
    entry = Entry('article', EXAMPLE_ENTRY_DICT)
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


def test_match_with_wrong_key():
    """Asserts issue #1 is fixed.

    When matches() is called with a key in the filter which does not exist in the entry, the key
    should be ignored and the function should return normally.
    """
    entry = Entry('article', EXAMPLE_ENTRY_DICT)
    _filter = {('tags', False): ['test']}
    assert entry.matches(_filter, _or=False)


@pytest.mark.parametrize('month_type', [int, str])
def test_month_conversion(month_type):
    """Test month conversion.

    Args:
        month_type (str): type to use for storing the 'month' field.
    """
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    config.database.format.month = month_type
    reference = EXAMPLE_ENTRY_DICT.copy()
    if month_type == str:
        reference['month'] = 'aug'
    entries = BibtexParser().parse('test/example_entry_unescaped.bib')
    entry = list(entries.values())[0]
    entry.convert_month(month_type)
    entry.escape_special_chars()
    assert entry.data == reference


def test_unchanged_umlaut_in_label():
    """Test unchanged Umlaut in labels."""
    root = path.abspath(path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    reference = {
        'ENTRYTYPE': 'book',
        'ID': 'LaTeX_Einführung',
        'title': 'LaTeX Einf{\\"u}hrung',
    }
    entries = BibtexParser().parse('test/example_entry_umlaut.bib')
    entry = list(entries.values())[0]
    entry.escape_special_chars()
    assert entry.data == reference


def test_database_singleton():
    """Test the Database is a Singleton."""
    bib = Database()
    bib2 = Database()
    assert bib is bib2
