"""coBib's BibTeX importer.

.. include:: ../man/cobib-bibtex.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import BibtexParser

from .base_importer import Importer

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class BibtexImporter(Importer):
    """The BibTeX Importer.

    This importer can parse the following arguments:

        * `file`: the BibTeX file from which to import entries.
    """

    name = "bibtex"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="bibtex",
            description="BibTeX importer.",
            epilog="Read cobib-bibtex.7 for more help.",
        )
        parser.add_argument("file", type=str, help="the BibTeX file from which to import")

        cls.argparser = parser

    @override
    async def fetch(self) -> list[Entry]:
        LOGGER.debug("Starting BibTeX import.")

        Event.PreBibtexImport.fire(self)

        self.imported_entries = list(BibtexParser().parse(self.largs.file).values())

        Event.PostBibtexImport.fire(self)

        return self.imported_entries
