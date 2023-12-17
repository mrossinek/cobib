"""Tests for coBib's BibtexParser."""


from __future__ import annotations

from itertools import zip_longest
from typing import Dict, Optional

import pytest

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import BibtexParser

from .parser_test import ParserTest


class TestBibtexParser(ParserTest):
    """Tests for coBib's BibtexParser."""

    @pytest.mark.parametrize("encode_latex", [True, False])
    def test_to_bibtex(self, encode_latex: bool) -> None:
        """Test to bibtex conversion.

        Args:
            encode_latex: whether to encode Unicode characters using LaTeX sequences.
        """
        entry = Entry(
            "LaTeX_Einfuhrung",
            {
                "ENTRYTYPE": "book",
                "author": "Mustermann, Max and Müller, Mara",
                "title": 'LaTeX Einf{\\"u}hrung',
            },
        )

        entry_str = BibtexParser(encode_latex).dump(entry)

        expected = [
            "@book{LaTeX_Einfuhrung,",
            " author = {Mustermann, Max and Müller, Mara},",
            ' title = {LaTeX Einf{\\"u}hrung}',
            "}",
        ]
        if encode_latex:
            expected[1] = ' author = {Mustermann, Max and M{\\"u}ller, Mara},'

        for line, truth in zip_longest(entry_str.split("\n"), expected):
            if not line:
                continue
            assert line == truth.strip("\n")

    def test_from_bibtex_str(self) -> None:
        """Test parsing a bibtex string."""
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        with open(self.EXAMPLE_BIBTEX_FILE, "r", encoding="utf-8") as file:
            bibtex_str = file.read()
        entries = BibtexParser().parse(bibtex_str)
        entry = next(iter(entries.values()))
        assert entry.data == reference

    def test_from_bibtex_file(self) -> None:
        """Test parsing a bibtex file."""
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        entries = BibtexParser().parse(self.EXAMPLE_BIBTEX_FILE)
        entry = next(iter(entries.values()))
        assert entry.data == reference

    def test_event_pre_bibtex_parse(self) -> None:
        """Tests the PreBibtexParse event."""

        @Event.PreBibtexParse.subscribe
        def hook(string: str) -> Optional[str]:
            with open(self.EXAMPLE_BIBTEX_FILE, "r", encoding="utf-8") as file:
                return file.read()

        assert Event.PreBibtexParse.validate()

        reference = self.EXAMPLE_ENTRY_DICT.copy()
        entries = BibtexParser().parse("Hello world!")

        entry = next(iter(entries.values()))
        assert entry.data == reference

    def test_event_post_bibtex_parse(self) -> None:
        """Tests the PostBibtexParse event."""

        @Event.PostBibtexParse.subscribe
        def hook(bib: Dict[str, Entry]) -> None:
            bib["Cao_2019"].data["month"] = "August"

        assert Event.PostBibtexParse.validate()

        reference = self.EXAMPLE_ENTRY_DICT.copy()
        reference["month"] = "August"

        with open(self.EXAMPLE_BIBTEX_FILE, "r", encoding="utf-8") as file:
            bibtex_str = file.read()
        entries = BibtexParser().parse(bibtex_str)
        entry = next(iter(entries.values()))
        assert entry.data == reference

    def test_event_pre_bibtex_dump(self) -> None:
        """Tests the PreBibtexDump event."""

        @Event.PreBibtexDump.subscribe
        def hook(entry: Entry) -> None:
            entry.label = "Cao2019"

        assert Event.PreBibtexDump.validate()

        entry = Entry("Cao_2019", self.EXAMPLE_ENTRY_DICT.copy())
        entry_str = BibtexParser().dump(entry)
        assert entry_str.split("\n")[0] == "@article{Cao2019,"

    def test_event_post_bibtex_dump(self) -> None:
        """Tests the PostBibtexDump event."""

        @Event.PostBibtexDump.subscribe
        def hook(string: str) -> Optional[str]:
            return "Hello world!"

        assert Event.PostBibtexDump.validate()

        entry = Entry("Cao_2019", self.EXAMPLE_ENTRY_DICT.copy())
        entry_str = BibtexParser().dump(entry)
        assert entry_str == "Hello world!"
