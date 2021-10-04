"""coBib's BibTex parser.

This parser leverages the [`bibtexparser`](https://pypi.org/project/bibtexparser/) library to
convert between `cobib.database.Entry` instances and raw BibTex strings.

Non-standard BibTex types can be configured to be ignored via
`config.parsers.bibtex.ignore_non_standard_types`.

The parser is registered under the `-b` and `--bibtex` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

import logging
from collections import OrderedDict
from typing import Dict

import bibtexparser

from cobib.config import Event, config
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class BibtexParser(Parser):
    """The BibTex Parser."""

    name = "bibtex"

    def parse(self, string: str) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102

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
            bib[label] = Entry(label, entry)

        Event.PostBibtexParse.fire(bib)

        return bib

    def dump(self, entry: Entry) -> str:
        # pdoc will inherit the docstring from the base class
        # noqa: D102

        Event.PreBibtexDump.fire(entry)

        database = bibtexparser.bibdatabase.BibDatabase()
        stringified_entry = entry.stringify()
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
