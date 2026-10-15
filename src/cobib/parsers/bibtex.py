"""coBib's BibTex parser.

.. include:: ../man/cobib-bibtex.7.html_fragment
"""

from __future__ import annotations

import logging
from collections import OrderedDict

import bibtexparser
from bibtexparser.library import Library
from bibtexparser.middlewares import NormalizeFieldKeys, RemoveEnclosingMiddleware
from bibtexparser.model import Entry as BibtexEntry
from bibtexparser.model import Field
from bibtexparser.writer import BibtexFormat
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)
"""@private module logger."""

STANDARD_ENTRY_TYPES = frozenset(
    {
        "article",
        "book",
        "booklet",
        "conference",
        "inbook",
        "incollection",
        "inproceedings",
        "manual",
        "mastersthesis",
        "misc",
        "phdthesis",
        "proceedings",
        "techreport",
        "unpublished",
    }
)
"""@private The entry types which are considered standard. In bibtexparser 1.X, this was the set of
types which were retained when `ignore_nonstandard_types` was enabled. Version 2.X no longer
filters entry types itself, so coBib needs to do so."""


def strip_after_new_lines(value: str) -> str:
    """Removes leading whitespace from all but the first line of a value.

    bibtexparser 2.X retains the indentation of continuation lines within multi-line values, whereas
    version 1.X stripped it. This function reproduces the behavior of the latter.

    Args:
        value: the value to process.

    Returns:
        The processed value.
    """
    lines = value.splitlines()
    if len(lines) > 1:
        lines = [lines[0]] + [line.lstrip() for line in lines[1:]]
        return "\n".join(lines)
    return value


class BibtexParser(Parser):
    """The BibTex Parser."""

    name = "bibtex"

    def __init__(self, encode_latex: bool = True, inline_note: bool = False) -> None:
        """Initializes a parser instance.

        Args:
            encode_latex: whether to encode non-ASCII characters using LaTeX sequences.
            inline_note: whether to inline the content of the entry's associated note file.
        """
        self.encode_latex = encode_latex
        """Whether to encode non-ASCII characters using LaTeX sequences. For more details see
        `cobib.database.entry.Entry.stringify`."""

        self.inline_note = inline_note
        """Whether to inline the content of the entry's associated note file. For more details see
        `cobib.database.entry.Entry.stringify`."""

    @override
    def parse(self, string: str) -> dict[str, Entry]:
        string = Event.PreBibtexParse.fire(string) or string

        try:
            LOGGER.debug("Loading BibTex data from file: %s.", string)
            with open(string, "r", encoding="utf-8") as file:
                bibtex_string = file.read()
        except (OSError, FileNotFoundError):
            LOGGER.debug("Loading BibTex string: %s.", string)
            bibtex_string = string

        # NOTE: we deliberately do NOT use the default parse stack because it would resolve string
        # references (e.g. `month = jan`), whereas coBib wants to retain them verbatim. Removing the
        # enclosing characters (braces or quotes) from all values is the only transformation needed.
        library = bibtexparser.parse_string(  # type: ignore[attr-defined]
            bibtex_string,
            parse_stack=[
                NormalizeFieldKeys(),
                RemoveEnclosingMiddleware(),
            ],
        )

        for failed_block in library.failed_blocks:
            LOGGER.warning(
                "Skipping a BibTex block which failed to parse: %s",
                getattr(failed_block, "error", failed_block),
            )

        ignore_non_standard_types = config.parsers.bibtex.ignore_non_standard_types

        bib: OrderedDict[str, Entry] = OrderedDict()
        for bib_entry in library.entries:
            entry_type = bib_entry.entry_type.lower()
            if ignore_non_standard_types and entry_type not in STANDARD_ENTRY_TYPES:
                LOGGER.warning(
                    "Ignoring entry %s of non-standard type '%s'.", bib_entry.key, entry_type
                )
                continue

            data: dict[str, str] = {"ENTRYTYPE": entry_type}
            for field in bib_entry.fields:
                # NOTE: unquoted integers and string references (such as `month = jan`) are kept
                # as they appear in the source, but we ensure that all values are strings.
                data[field.key] = strip_after_new_lines(str(field.value))

            actual_entry = Entry(bib_entry.key, data)
            bib[actual_entry.label] = actual_entry

        Event.PostBibtexParse.fire(bib)

        return bib

    @override
    def dump(self, entry: Entry) -> str:
        Event.PreBibtexDump.fire(entry)

        stringified_entry = entry.stringify(
            encode_latex=self.encode_latex, inline_note=self.inline_note
        )
        label = stringified_entry.pop("label")
        entry_type = stringified_entry.pop("ENTRYTYPE")

        # NOTE: bibtexparser 1.X sorted all fields alphabetically when writing. We retain that.
        fields = []
        for key in sorted(stringified_entry.keys()):
            value = stringified_entry[key]
            if key == "month":
                # Month values are written as bare string references (e.g. `month = jan`).
                fields.append(Field(key, value, enclosing="no-enclosing"))
            else:
                fields.append(Field(key, value))

        library = Library()
        library.add(BibtexEntry(entry_type, label, fields))

        LOGGER.debug("Converting entry %s to BibTex format.", entry.label)

        # NOTE: these settings reproduce the formatting which bibtexparser 1.X used by default.
        bibtex_format = BibtexFormat()  # type: ignore[no-untyped-call]
        bibtex_format.indent = " "
        bibtex_format.block_separator = "\n"
        # NOTE: the amount of trailing whitespace which the writer emits differs between versions.
        # Thus, we normalize it to exactly one trailing line break, as in bibtexparser 1.X.
        string: str = bibtexparser.write_string(  # type: ignore[attr-defined]
            library, bibtex_format=bibtex_format
        )
        string = string.rstrip("\n") + "\n"

        string = Event.PostBibtexDump.fire(string) or string

        return string
