"""coBib's arXiv parser.

This parser is capable of generating `cobib.database.Entry` instances from a given arXiv ID.
It gathers the BibTex-encoded data from the arXiv API and parses the raw XML data.

The parser is registered under the `-a` and `--arxiv` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

import logging
import re
import sys
from collections import OrderedDict
from typing import Any, Dict

import requests
from bs4 import BeautifulSoup

from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class ArxivParser(Parser):
    """The arXiv Parser."""

    name = "arxiv"

    ARXIV_URL = "https://export.arxiv.org/api/query?id_list="
    """arXiv exporting URL taken from [here](https://arxiv.org/help/oa)."""

    def parse(self, string: str) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.info("Gathering BibTex data for arXiv ID: %s.", string)
        try:
            page = requests.get(self.ARXIV_URL + string, timeout=10)
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the arXiv ID: %s.", string)
            LOGGER.error(err)
            return OrderedDict()
        xml = BeautifulSoup(page.text, features="html.parser")
        if xml.feed.entry.title.contents[0] == "Error":
            msg = (
                "The arXiv API returned the following error: " + xml.feed.entry.summary.contents[0]
            )
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return OrderedDict()
        label = ""
        entry: Dict[str, Any] = {}
        entry["archivePrefix"] = "arXiv"
        for key in xml.feed.entry.findChildren(recursive=False):
            if key.name == "arxiv:doi":
                entry["doi"] = str(key.contents[0])
            elif key.name == "id":
                entry["arxivid"] = str(key.contents[0]).replace("http://arxiv.org/abs/", "")
                entry["eprint"] = str(key.contents[0])
            elif key.name == "arxiv:primary_category":
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
                if "author" not in entry.keys():
                    first = True
                    entry["author"] = ""
                name = [n.contents[0] for n in key.findChildren()][0]
                if first:
                    label = name.split()[-1] + label
                    first = False
                entry["author"] += "{} and ".format(name)
            elif key.name == "summary":
                entry["abstract"] = re.sub(r"\s+", " ", key.contents[0].strip().replace("\n", " "))
            else:
                LOGGER.warning("The key '%s' of this arXiv entry is not being processed!", key.name)
        if "doi" in entry.keys():
            entry["ENTRYTYPE"] = "article"
        else:
            entry["ENTRYTYPE"] = "unpublished"
        # strip last 'and' from author field
        entry["author"] = entry["author"][:-5]
        bib = OrderedDict()
        bib[label] = Entry(label, entry)
        return bib

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as an arXiv ID."""
        LOGGER.error("Cannot dump an entry as an arXiv ID.")
