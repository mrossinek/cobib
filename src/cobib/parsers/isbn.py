"""ISBN Parser."""

import json
import logging
import re
import sys
from collections import OrderedDict

import requests

from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class ISBNParser(Parser):
    """The ISBN Parser."""

    name = "isbn"

    # ISBN regex used for matching ISBNs (adapted from https://github.com/xlcnd/isbnlib)
    ISBN_REGEX = re.compile(
        r"97[89]{1}(?:-?\d){10}|\d{9}[0-9X]{1}|" r"[-0-9X]{10,16}", re.I | re.M | re.S
    )
    # ISBN-API: https://openlibrary.org/dev/docs/api/books
    ISBN_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:"

    def parse(self, string):
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
            return {}
        try:
            contents = dict(json.loads(page.content))
        except json.JSONDecodeError as err:
            LOGGER.error("An Exception occurred while parsing the query results: %s.", page.content)
            LOGGER.error(err)
            return {}
        if not contents:
            msg = (
                f'No data was found for ISBN "{string}". If you think this is an error and '
                + "the openlibrary API should provide an entry, please file a bug report. "
                + "Otherwise please try adding this entry manually until more APIs are "
                + "available in coBib."
            )
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return {}
        entry = {}
        for key, value in contents[list(contents.keys())[0]].items():
            if key in ["title", "url"]:
                entry[key] = value
            elif key == "number_of_pages":
                # we explicitly convert to a string to prevent type errors in the bibtexparser
                entry["pages"] = str(value)
            elif key == "publish_date":
                entry["date"] = value
                try:
                    entry["year"] = re.search(r"\d{4}", value).group()
                    if "ID" in entry.keys():
                        entry["ID"] += str(entry["year"])
                    else:
                        entry["ID"] = str(entry["year"])
                except AttributeError:
                    pass
            elif key == "authors":
                if "ID" in entry.keys():
                    entry["ID"] = value[0]["name"].split()[-1] + entry["ID"]
                else:
                    entry["ID"] = value[0]["name"].split()[-1]
                entry["author"] = " and".join([a["name"] for a in value])
            elif key == "publishers":
                entry["publisher"] = " and".join([a["name"] for a in value])
        # set entry-type do 'book'
        entry["ENTRYTYPE"] = "book"
        bib = OrderedDict()
        bib[entry["ID"]] = Entry(entry["ID"], entry)
        return bib

    def dump(self, entry):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.error("Cannot dump an entry as an ISBN.")
