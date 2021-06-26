"""coBib's DOI parser.

This parser is capable of generating `cobib.database.Entry` instances from a given DOI.
It gathers the BibTex-encoded data from https://doi.org/ and parses it directly using the
`cobib.parsers.bibtex.BibtexParser`.

Since v3.2.0 coBib will also attempt to download the PDF version of the new entry. You can
configure the default download location via `config.utils.file_downloader.default_location`.
Since in general the PDF may not be freely available, your mileage with this feature may vary. Until
coBib supports internal proxy configurations, make sure you are logged in to a VPN for the smoothest
experience with closed-source journals.
Furthermore, you should look into the `config.utils.file_downloader.url_map` setting, through which
you tell coBib how to map from journal landing page URLs to the corresponding PDF URLs. For more
information check out `cobib.config.example` and the man-page.

The parser is registered under the `-d` and `--doi` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

import logging
import re
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
            return OrderedDict()
        LOGGER.info("Gathering BibTex data for DOI: %s.", string)
        try:
            page = requests.get(self.DOI_URL + string, headers=self.DOI_HEADER, timeout=10)
            # this assumes that the doi.org page redirects to the correct journal's landing page
            redirected_url = requests.head(self.DOI_URL + string, timeout=1).headers["Location"]
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the DOI: %s.", string)
            LOGGER.error(err)
            return OrderedDict()
        bib = BibtexParser().parse(page.text)
        for entry in bib.values():
            entry.data["_download"] = redirected_url
        return bib

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as a DOI."""
        LOGGER.error("Cannot dump an entry as a DOI.")
