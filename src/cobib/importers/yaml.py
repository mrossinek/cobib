"""coBib's YAML importer.

.. include:: ../man/cobib-yaml.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import YAMLParser

from .base_importer import Importer

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class YAMLImporter(Importer):
    """The YAML Importer.

    This importer can parse the following arguments:

        * `file`: the YAML file from which to import entries.
    """

    name = "yaml"

    @override
    def __init__(self, *args: str, skip_download: bool = False) -> None:
        super().__init__(*args, skip_download=skip_download)

        self._imported_entries: list[Entry] = []

    @property
    @override
    def imported_entries(self) -> list[Entry]:
        return self._imported_entries

    @imported_entries.setter
    @override
    def imported_entries(self, entries: list[Entry]) -> None:
        self._imported_entries = entries

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="yaml",
            description="YAML importer.",
            epilog="Read cobib-yaml.7 for more help.",
        )
        parser.add_argument("file", type=str, help="the YAML file from which to import")

        cls.argparser = parser

    @override
    async def fetch(self) -> list[Entry]:
        LOGGER.debug("Starting YAML import.")

        Event.PreYAMLImport.fire(self)

        self.imported_entries = list(YAMLParser().parse(self.largs.file).values())

        Event.PostYAMLImport.fire(self)

        return self.imported_entries
