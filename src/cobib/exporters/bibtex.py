"""coBib's BibTeX exporter.

.. include:: ../man/cobib-bibtex.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import BibtexParser
from cobib.utils.journal_abbreviations import JournalAbbreviations

from .base_exporter import Exporter

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class BibtexExporter(Exporter):
    """The BibTeX Exporter.

    This exporter can parse the following arguments:

        * `file`: the BibTeX file into which to export entries.
        * `-a`, `--abbreviate`: abbreviate the Journal names before exporting. See also
          `cobib.config.config.UtilsConfig.journal_abbreviations`.
        * `--dotless`: remove punctuation from the Journal abbreviations.
    """

    name = "bibtex"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="bibtex",
            description="BibTeX exporter.",
            epilog="Read cobib-bibtex.7 for more help.",
        )
        parser.add_argument(
            "file", type=argparse.FileType("a"), help="the BibTeX file into which to export"
        )
        parser.add_argument(
            "-a", "--abbreviate", action="store_true", help="Abbreviate journal names"
        )
        parser.add_argument(
            "--dotless", action="store_true", help="Remove punctuation from journal abbreviations"
        )

        cls.argparser = parser

    @override
    def write(self, entries: list[Entry]) -> None:
        LOGGER.debug("Starting BibTeX export.")

        self.exported_entries = entries

        Event.PreBibtexExport.fire(self)

        bibtex_parser = BibtexParser()

        for entry in self.exported_entries:
            LOGGER.info('Exporting entry "%s".', entry.label)
            if self.largs.abbreviate and "journal" in entry.data.keys():
                entry.data["journal"] = JournalAbbreviations.abbreviate(
                    entry.data["journal"], dotless=self.largs.dotless
                )
            entry_str = bibtex_parser.dump(entry)
            self.largs.file.write(entry_str)

        Event.PostBibtexExport.fire(self)

        self.largs.file.close()
