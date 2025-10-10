"""coBib's Zip exporter.

.. include:: ../man/cobib-zip.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging
from zipfile import ZipFile

from typing_extensions import override

from cobib.config import Event, config
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
        parser.add_argument("file", type=str, help="the Zip file into which to export")
        files_group = parser.add_mutually_exclusive_group()
        files_group.add_argument(
            "--skip-files",
            action="store_true",
            default=None,
            help="do NOT include file attachments in the Zip archive",
        )
        files_group.add_argument(
            "--include-files",
            dest="skip_files",
            action="store_false",
            default=None,
            help="DO include file attachments in the Zip archive",
        )
        notes_group = parser.add_mutually_exclusive_group()
        notes_group.add_argument(
            "--skip-notes",
            action="store_true",
            default=None,
            help="do NOT include external notes in the Zip archive",
        )
        notes_group.add_argument(
            "--include-notes",
            dest="skip_notes",
            action="store_false",
            default=None,
            help="DO include external notes in the Zip archive",
        )

        cls.argparser = parser

    @override
    def write(self, entries: list[Entry]) -> None:
        LOGGER.debug("Starting Zip export.")

        self.exported_entries = entries

        self.largs.file = ZipFile(self.largs.file, "a")

        Event.PreZipExport.fire(self)

        skip_files = config.exporters.zip.skip_files
        if self.largs.skip_files is not None:
            skip_files = self.largs.skip_files
        LOGGER.debug(
            "The Zip archive will%s include file attachments.", " NOT" if skip_files else ""
        )

        skip_notes = config.exporters.zip.skip_notes
        if self.largs.skip_notes is not None:
            skip_notes = self.largs.skip_notes
        LOGGER.debug("The Zip archive will%s include external notes.", " NOT" if skip_notes else "")

        for entry in self.exported_entries:
            if not skip_files:
                for file in entry.file:
                    path = RelPath(file).path
                    LOGGER.info(
                        'Adding "%s" associated with "%s" to the zip file.', path, entry.label
                    )
                    self.largs.file.write(path, path.name)
            if not skip_notes and entry.notes is not None:
                path = RelPath(entry.notes).path
                LOGGER.info('Adding "%s" associated with "%s" to the zip file.', path, entry.label)
                self.largs.file.write(path, path.name)

        Event.PostZipExport.fire(self)

        self.largs.file.close()
