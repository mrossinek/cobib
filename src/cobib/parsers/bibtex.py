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

from cobib.config import config
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class BibtexParser(Parser):
    """The BibTex Parser."""

    name = "bibtex"

    def parse(self, string: str) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        bparser = bibtexparser.bparser.BibTexParser()
        bparser.ignore_nonstandard_types = config.parsers.bibtex.ignore_non_standard_types
        try:
            LOGGER.debug("Loading BibTex data from file: %s.", string)
            with open(string, "r") as file:
                database = bibtexparser.load(file, parser=bparser)
        except (OSError, FileNotFoundError):
            LOGGER.debug("Loading BibTex string: %s.", string)
            database = bibtexparser.loads(string, parser=bparser)
        bib = OrderedDict()
        for entry in database.entries:
            bib[entry["ID"]] = Entry(entry["ID"], entry)
        return bib

    def dump(self, entry: Entry) -> str:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        database = bibtexparser.bibdatabase.BibDatabase()
        database.entries = [entry.data]
        LOGGER.debug("Converting entry %s to BibTex format.", entry.label)
        string: str = bibtexparser.dumps(database)
        return string
