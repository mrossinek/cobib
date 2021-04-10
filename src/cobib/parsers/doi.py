"""coBib's DOI parser.

This parser is capable of generating `cobib.database.Entry` instances from a given DOI.
It gathers the BibTex-encoded data from https://doi.org/ and parses it directly using the
`cobib.parsers.bibtex.BibtexParser`.

The parser is registered under the `-d` and `--doi` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

import logging
import re
import sys
from collections import OrderedDict
from typing import Dict

import requests

from cobib.database import Entry

from .base_parser import Parser
from .bibtex import BibtexParser

LOGGER = logging.getLogger(__name__)


class DOIParser(Parser):
    """The DOI Parser."""

    name = "doi"

    DOI_URL = "https://doi.org/"
    """The DOI 'API' URL."""
    DOI_HEADER = {"Accept": "application/x-bibtex"}
    """The DOI 'API' header taken from [here](https://crosscite.org/docs.html)."""
    DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
    """A regex pattern used to match valid DOIs."""

    def parse(self, string: str) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        try:
            assert re.match(self.DOI_REGEX, string)
        except AssertionError:
            msg = f"'{string}' is not a valid DOI."
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return OrderedDict()
        LOGGER.info("Gathering BibTex data for DOI: %s.", string)
        try:
            page = requests.get(self.DOI_URL + string, headers=self.DOI_HEADER, timeout=10)
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the DOI: %s.", string)
            LOGGER.error(err)
            return OrderedDict()
        return BibtexParser().parse(page.text)

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as a DOI."""
        LOGGER.error("Cannot dump an entry as a DOI.")
