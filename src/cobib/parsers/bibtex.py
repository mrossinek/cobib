"""coBib's BibTex parser.

.. include:: ../man/cobib-bibtex.7.html_fragment
"""

from __future__ import annotations

import logging
from collections import OrderedDict

import bibtexparser
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class BibtexParser(Parser):
    """The BibTex Parser."""

    name = "bibtex"

    def __init__(self, encode_latex: bool = True, inline_note: bool = False) -> None:
        """Initializes a parser instance.

        Args:
            encode_latex: whether to encode non-ASCII characters using LaTeX sequences.
            inline_note: whether to inline the content of the entry's associated note file.
        """
        self.encode_latex = encode_latex
        """Whether to encode non-ASCII characters using LaTeX sequences. For more details see
        `cobib.database.entry.Entry.stringify`."""

        self.inline_note = inline_note
        """Whether to inline the content of the entry's associated note file. For more details see
        `cobib.database.entry.Entry.stringify`."""

    @override
    def parse(self, string: str) -> dict[str, Entry]:
        string = Event.PreBibtexParse.fire(string) or string

        bparser = bibtexparser.bparser.BibTexParser()
        bparser.ignore_nonstandard_types = config.parsers.bibtex.ignore_non_standard_types
        bparser.common_strings = True
        bparser.interpolate_strings = False
        try:
            LOGGER.debug("Loading BibTex data from file: %s.", string)
            with open(string, "r", encoding="utf-8") as file:
                database = bibtexparser.load(file, parser=bparser)
        except (OSError, FileNotFoundError):
            LOGGER.debug("Loading BibTex string: %s.", string)
            database = bibtexparser.loads(string, parser=bparser)
        bib = OrderedDict()
        for entry in database.entries:
            if "month" in entry.keys() and isinstance(
                entry["month"], bibtexparser.bibtexexpression.BibDataStringExpression
            ):
                entry["month"] = entry["month"].expr[0].name
            label = entry.pop("ID")
            actual_entry = Entry(label, entry)
            bib[actual_entry.label] = actual_entry

        Event.PostBibtexParse.fire(bib)

        return bib

    @override
    def dump(self, entry: Entry) -> str:
        Event.PreBibtexDump.fire(entry)

        database = bibtexparser.bibdatabase.BibDatabase()
        stringified_entry = entry.stringify(
            encode_latex=self.encode_latex, inline_note=self.inline_note
        )
        stringified_entry["ID"] = stringified_entry.pop("label")
        if "month" in stringified_entry.keys():
            # convert month to bibtexexpression
            stringified_entry["month"] = bibtexparser.bibtexexpression.BibDataStringExpression(
                [bibtexparser.bibdatabase.BibDataString(database, stringified_entry["month"])]
            )
        database.entries = [stringified_entry]
        LOGGER.debug("Converting entry %s to BibTex format.", entry.label)
        writer = bibtexparser.bwriter.BibTexWriter()
        writer.common_strings = True
        string: str = writer.write(database)

        string = Event.PostBibtexDump.fire(string) or string

        return string
