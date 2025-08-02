"""coBib's URL parser.

.. include:: ../man/cobib-url.7.html_fragment
"""

from __future__ import annotations

import logging
import re
from collections import Counter, OrderedDict

import requests
from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry

from .arxiv import ARXIV_REGEX, ArxivParser
from .base_parser import Parser
from .doi import DOI_REGEX, DOIParser
from .isbn import ISBN_REGEX, ISBNParser

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class URLParser(Parser):
    """The URL Parser."""

    name = "url"

    @override
    def parse(self, string: str) -> dict[str, Entry]:
        string = Event.PreURLParse.fire(string) or string

        if re.search(ARXIV_REGEX, string):
            LOGGER.debug("URL contains an arXiv ID")
            entries = ArxivParser().parse(string)
            if entries:  # pragma: no branch
                LOGGER.debug("Successfully extracted metadata from URL with ArxivParser")
                return entries
        if re.search(DOI_REGEX, string):
            LOGGER.debug("URL contains a DOI")
            entries = DOIParser().parse(string)
            if entries:  # pragma: no branch
                LOGGER.debug("Successfully extracted metadata from URL with DOIParser")
                return entries
        if re.search(ISBN_REGEX, string):
            LOGGER.debug("URL contains an ISBN")
            entries = ISBNParser().parse(string)
            if entries:  # pragma: no branch
                LOGGER.debug("Successfully extracted metadata from URL with ISBNParser")
                return entries

        try:
            session = requests.Session()
            page = session.get(string, timeout=10)
            if page.encoding is None:
                page.encoding = "utf-8"
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the URL: %s.", string)
            LOGGER.error(err)
            return OrderedDict()

        LOGGER.debug("Falling back to determining most common DOI in URLs page contents")
        matches = re.findall(DOI_REGEX, page.text)
        dois = Counter(matches)
        if not dois:
            LOGGER.error("Could not find any DOIs on the URLs page: %s", string)
            return OrderedDict()
        # we assume the most common DOI on the page is the one which we are looking for
        most_common_doi = dois.most_common(1)[0]
        LOGGER.debug("Most common DOI is: %s", most_common_doi)
        if most_common_doi[1] > 1:
            entries = DOIParser().parse(most_common_doi[0])

        if entries:
            Event.PostURLParse.fire(entries)

            LOGGER.debug("Successfully extracted metadata from most common DOI")
            return entries

        LOGGER.error("Could not extract metadata from URL: %s", string)
        return OrderedDict()

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as a URL."""
        LOGGER.error("Cannot dump an entry as a URL.")
