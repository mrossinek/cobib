"""coBib's Zip exporter.

.. include:: ../man/cobib-zip.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging
from zipfile import ZipFile

from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry
from cobib.utils.rel_path import RelPath

from .base_exporter import Exporter

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ZipExporter(Exporter):
    """The Zip Exporter.

    This exporter can parse the following arguments:

        * `file`: the Zip file into which to export entries.
    """

    name = "zip"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="zip",
            description="Zip exporter.",
            epilog="Read cobib-zip.7 for more help.",
        )
        parser.add_argument(
            "file", type=argparse.FileType("a"), help="the Zip file into which to export"
        )

        cls.argparser = parser

    @override
    def write(self, entries: list[Entry]) -> None:
        LOGGER.debug("Starting Zip export.")

        self.exported_entries = entries

        self.largs.file = ZipFile(self.largs.file.name, "a")

        Event.PreZipExport.fire(self)

        for entry in self.exported_entries:
            if "file" in entry.data.keys() and entry.file is not None:
                for file in entry.file:
                    path = RelPath(file).path
                    LOGGER.info(
                        'Adding "%s" associated with "%s" to the zip file.', path, entry.label
                    )
                    self.largs.file.write(path, path.name)

        Event.PostZipExport.fire(self)

        self.largs.file.close()
