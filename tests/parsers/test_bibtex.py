"""Tests for coBib's BibtexParser."""
# pylint: disable=no-self-use,unused-argument

import pytest

from cobib import parsers

from .parser_test import ParserTest


class TestBibtexParser(ParserTest):
    """Tests for coBib's BibtexParser."""

    def test_to_bibtex(self) -> None:
        """Test to bibtex conversion."""
        pytest.skip("Testing this string is a bit ambigious. Assumed to be tested by bibtexparser.")

    def test_from_bibtex_str(self) -> None:
        """Test parsing a bibtex string."""
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        with open(self.EXAMPLE_BIBTEX_FILE, "r", encoding="utf-8") as file:
            bibtex_str = file.read()
        entries = parsers.BibtexParser().parse(bibtex_str)
        entry = list(entries.values())[0]
        assert entry.data == reference

    def test_from_bibtex_file(self) -> None:
        """Test parsing a bibtex file."""
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        entries = parsers.BibtexParser().parse(self.EXAMPLE_BIBTEX_FILE)
        entry = list(entries.values())[0]
        assert entry.data == reference
