"""Bibtex Parser."""

import logging
from collections import OrderedDict

import bibtexparser

from cobib.config import config
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class BibtexParser(Parser):
    """The Bibtex Parser."""

    name = "bibtex"

    def parse(self, string):
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

    def dump(self, entry):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        database = bibtexparser.bibdatabase.BibDatabase()
        database.entries = [entry.data]
        LOGGER.debug("Converting entry %s to BibTex format.", entry.label)
        return bibtexparser.dumps(database)
