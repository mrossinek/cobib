"""DOI Parser."""

import logging
import re
import sys

import requests

from .base_parser import Parser
from .bibtex import BibtexParser

LOGGER = logging.getLogger(__name__)


class DOIParser(Parser):
    """The DOI Parser."""

    name = "doi"

    # API and HEADER settings according to this resource: https://crosscite.org/docs.html
    DOI_URL = "https://doi.org/"
    DOI_HEADER = {"Accept": "application/x-bibtex"}
    # DOI regex used for matching DOIs
    DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'

    def parse(self, string):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        try:
            assert re.match(self.DOI_REGEX, string)
        except AssertionError:
            msg = f"'{string}' is not a valid DOI."
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return {}
        LOGGER.info("Gathering BibTex data for DOI: %s.", string)
        try:
            page = requests.get(self.DOI_URL + string, headers=self.DOI_HEADER, timeout=10)
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the DOI: %s.", string)
            LOGGER.error(err)
            return {}
        return BibtexParser().parse(page.text)

    def dump(self, entry):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.error("Cannot dump an entry as a DOI.")
