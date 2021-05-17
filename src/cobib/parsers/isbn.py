"""coBib's ISBN parser.

This parser is capable of generating `cobib.database.Entry` instances from a given ISBN.
It gathers the BibTex-encoded data from the ISBN API and parses the raw json data.

Note, that the openlibrary API does not contain all ISBNs and potential server errors will be caught
by the parser.
In the future, I hope to make the API backend configurable.

The parser is registered under the `-i` and `--isbn` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

import json
import logging
import re
import sys
from collections import OrderedDict
from typing import Dict

import requests

from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class ISBNParser(Parser):
    """The ISBN Parser."""

    name = "isbn"

    ISBN_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:"
    """ISBN API URL taken from [here](https://openlibrary.org/dev/docs/api/books)."""
    ISBN_REGEX = re.compile(
        r"97[89]{1}(?:-?\d){10}|\d{9}[0-9X]{1}|" r"[-0-9X]{10,16}", re.I | re.M | re.S
    )
    """A regex pattern used to match valid ISBNs. Adapted from
    [here](https://github.com/xlcnd/isbnlib)."""

    def parse(self, string: str) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        assert re.match(self.ISBN_REGEX, string)
        LOGGER.info("Gathering BibTex data for ISBN: %s.", string)
        isbn_plain = "".join([i for i in string if i.isdigit()])
        try:
            page = requests.get(self.ISBN_URL + isbn_plain + "&jscmd=data&format=json", timeout=10)
        except requests.exceptions.RequestException as err:
            LOGGER.error("An Exception occurred while trying to query the ISBN: %s.", string)
            LOGGER.error(err)
            return OrderedDict()
        try:
            contents = dict(json.loads(page.content))
        except json.JSONDecodeError as err:
            LOGGER.error("An Exception occurred while parsing the query results: %s.", page.content)
            LOGGER.error(err)
            return OrderedDict()
        if not contents:
            msg = (
                f'No data was found for ISBN "{string}". If you think this is an error and '
                + "the openlibrary API should provide an entry, please file a bug report. "
                + "Otherwise please try adding this entry manually until more APIs are "
                + "available in coBib."
            )
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return OrderedDict()
        label = ""
        entry = {}
        for key, value in contents[list(contents.keys())[0]].items():
            if key in ["title", "url"]:
                entry[key] = value
            elif key == "number_of_pages":
                # we explicitly convert to a string to prevent type errors in the bibtexparser
                str_val = str(value)
                entry["pages"] = int(str_val) if str_val.isnumeric() else str_val
            elif key == "publish_date":
                entry["date"] = value
                try:
                    match = re.search(r"\d{4}", value)
                    if match is None:
                        raise AttributeError  # pragma: no cover
                    entry["year"] = int(match.group())
                    label += str(entry["year"])
                except AttributeError:  # pragma: no cover
                    pass  # pragma: no cover
            elif key == "authors":
                label = value[0]["name"].split()[-1] + label
                entry["author"] = " and".join([a["name"] for a in value])
            elif key == "publishers":
                entry["publisher"] = " and".join([a["name"] for a in value])
        # set entry-type do 'book'
        entry["ENTRYTYPE"] = "book"
        bib = OrderedDict()
        bib[label] = Entry(label, entry)
        return bib

    def dump(self, entry: Entry) -> None:
        """We cannot dump a generic entry as an ISBN."""
        LOGGER.error("Cannot dump an entry as an ISBN.")
