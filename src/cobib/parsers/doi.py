"""coBib's DOI parser.

.. include:: ../man/cobib-doi.7.html_fragment
"""

from __future__ import annotations

import logging
import re
from collections import OrderedDict

import requests
from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry

from .base_parser import Parser
from .bibtex import BibtexParser

LOGGER = logging.getLogger(__name__)
"""@private module logger."""

DOI_URL = "https://doi.org/"
"""The DOI 'API' URL."""
DOI_HEADER = {"Accept": "application/x-bibtex"}
"""The DOI 'API' header taken from [here](https://crosscite.org/docs.html)."""
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'\?])\S)+)\b'
"""A regex pattern used to match valid DOIs."""

# Any HTTP status code above 400 indicates some form of error.
HTTP_ERROR_CODE = 400


class DOIParser(Parser):
    """The DOI Parser."""

    name = "doi"

    @override
    def parse(self, string: str) -> dict[str, Entry]:
        string = Event.PreDOIParse.fire(string) or string

        try:
            match = re.search(DOI_REGEX, string)
            if match is None:
                raise AssertionError
        except AssertionError:
            msg = f"'{string}' is not a valid DOI."
            LOGGER.warning(msg)
            return OrderedDict()
        doi = match.group(1)
        LOGGER.info("Gathering BibTex data for DOI: %s.", doi)
        try:
            session = requests.Session()
            LOGGER.debug("The queried URL is: '%s'", DOI_URL + doi)
            page = session.get(DOI_URL + doi, headers=DOI_HEADER, timeout=10)
            if page.status_code >= HTTP_ERROR_CODE:
                LOGGER.error(
                    "Querying the DOI URL returned the following error code: %s.", page.status_code
                )
                return OrderedDict()
            if page.encoding is None:
                page.encoding = "utf-8"
            # this assumes that the doi.org page redirects to the correct journal's landing page
            redirected_url: str = ""
            header = session.head(DOI_URL + doi, timeout=1).headers
            max_iter = 3
            while "Location" in header and max_iter:
                LOGGER.debug("The current DOI URL header: '%s'", header)
                max_iter -= 1
                redirected_url = header["Location"]
                if not redirected_url.startswith("http"):
                    LOGGER.debug(
                        "Even though the header still contains a 'Location', it is no longer a "
                        "valid URL to redirect to. Therefore, we assume that this current page "
                        "contains what we are looking for."
                    )
                    break
                LOGGER.debug("The found URL redirects to: '%s'", redirected_url)
                header = session.head(redirected_url, timeout=1).headers
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the DOI: %s.", doi)
            LOGGER.error(err)
            return OrderedDict()
        bib = BibtexParser().parse(page.text)
        if redirected_url:
            for entry in bib.values():
                entry.data["_download"] = redirected_url

        Event.PostDOIParse.fire(bib)

        return bib

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as a DOI."""
        LOGGER.error("Cannot dump an entry as a DOI.")
