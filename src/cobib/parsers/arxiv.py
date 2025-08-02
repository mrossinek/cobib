"""coBib's arXiv parser.

.. include:: ../man/cobib-arxiv.7.html_fragment
"""

from __future__ import annotations

import logging
import re
from collections import OrderedDict
from typing import Any

import requests
from bs4 import BeautifulSoup
from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)
"""@private module logger."""

ARXIV_URL = "https://export.arxiv.org/api/query?id_list="
"""arXiv exporting URL taken from [here](https://arxiv.org/help/oa)."""
ARXIV_REGEX = r"(\d{4}.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?\/\d{7})(v\d+)?"
"""A regex pattern used to match valid DOIs."""


class ArxivParser(Parser):
    """The arXiv Parser."""

    name = "arxiv"

    @override
    def parse(self, string: str) -> dict[str, Entry]:  # noqa: PLR0912
        string = Event.PreArxivParse.fire(string) or string

        try:
            match = re.search(ARXIV_REGEX, string)
            if match is None:
                raise AssertionError
        except AssertionError:
            msg = f"'{string}' is not a valid arXiv ID."
            LOGGER.warning(msg)
            return OrderedDict()
        arxiv_id = match.group(1)
        LOGGER.info("Gathering BibTex data for arXiv ID: %s.", arxiv_id)
        try:
            session = requests.Session()
            page = session.get(ARXIV_URL + arxiv_id, timeout=10)
            if page.encoding is None:
                page.encoding = "utf-8"
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the arXiv ID: %s.", arxiv_id)
            LOGGER.error(err)
            return OrderedDict()
        xml = BeautifulSoup(page.text, features="xml")
        if xml.feed.entry.title.contents[0] == "Error":  # type: ignore[union-attr]
            msg = (
                "The arXiv API returned the following error: " + xml.feed.entry.summary.contents[0]  # type: ignore[operator,union-attr]
            )
            LOGGER.warning(msg)
            return OrderedDict()
        label = ""
        entry: dict[str, Any] = {}
        entry["archivePrefix"] = "arXiv"
        for key in xml.feed.entry.find_all(recursive=False):  # type: ignore[union-attr]
            if "doi" in key.name:
                entry["doi"] = str(key.contents[0])
            elif key.name == "id":
                entry["arxivid"] = str(key.contents[0]).replace("http://arxiv.org/abs/", "")
                entry["eprint"] = str(key.contents[0])
            elif key.name == "primary_category":
                entry["primaryClass"] = str(key.attrs["term"])
            elif key.name == "published":
                # The year must also be stored as a string for compatibility reasons with
                # bibtexparser. However, we perform a conversion to an integer first, to ensure that
                # the year can actually be represented as such.
                entry["year"] = int(key.contents[0].split("-")[0])
                label += str(entry["year"])
            elif key.name == "title":
                entry["title"] = re.sub(r"\s+", " ", key.contents[0].strip().replace("\n", " "))
            elif key.name == "author":
                if "author" not in entry:
                    first = True
                    entry["author"] = ""
                name = next(n.contents[0] for n in key.find_all())
                if first:
                    label = name.split()[-1] + label
                    first = False
                entry["author"] += f"{name} and "
            elif key.name == "summary":
                entry["abstract"] = re.sub(r"\s+", " ", key.contents[0].strip().replace("\n", " "))
            elif key.name == "link":
                if key.attrs.get("title", None) == "doi":
                    entry["url"] = key.attrs["href"]
                elif key.attrs.get("title", None) == "pdf":
                    entry["_download"] = key.attrs.get("href", "")
            else:
                LOGGER.warning("The key '%s' of this arXiv entry is not being processed!", key.name)
        if "doi" in entry:
            entry["ENTRYTYPE"] = "article"
        else:
            entry["ENTRYTYPE"] = "unpublished"
        # strip last 'and' from author field
        entry["author"] = entry["author"][:-5]
        bib = OrderedDict()
        actual_entry = Entry(label, entry)
        bib[actual_entry.label] = actual_entry

        Event.PostArxivParse.fire(bib)

        return bib

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as an arXiv ID."""
        LOGGER.error("Cannot dump an entry as an arXiv ID.")
