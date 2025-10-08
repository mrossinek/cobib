"""coBib's BibTeX exporter.

.. include:: ../man/cobib-bibtex.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from typing_extensions import override

from cobib.config import Event, JournalFormat, config
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
        * `-f`, `--journal-format`:  specifies the output form of the `journal` field. This
          overwrites the `cobib.config.config.BibtexExporterConfig.journal_format` setting.
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
        abbrev_group = parser.add_mutually_exclusive_group()
        abbrev_group.add_argument(
            "-a",
            "--abbreviate",
            action="store_true",
            help="DEPRECATED: use '--journal-format abbrev' instead!",
        )
        abbrev_group.add_argument(
            "-f",
            "--journal-format",
            type=str,
            default=None,
            choices=[format.value for format in JournalFormat],
            help="the format to use for the 'journal' field",
        )
        parser.add_argument(
            "--dotless",
            action="store_true",
            help="DEPRECATED: use '--journal-format dotless' instead!",
        )

        cls.argparser = parser

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        largs = super()._parse_args(args)

        if largs.abbreviate:
            msg = (
                "The '--abbreviate' argument of the '--bibtex' exporter is deprecated! "
                "Instead you should use '--journal-format abbrev'."
            )
            LOGGER.warning(msg)
            largs.journal_format = "abbrev"

        if largs.dotless:
            msg = (
                "The '--dotless' argument of the '--bibtex' exporter is deprecated! "
                "Instead you should use '--journal-format dotless'."
            )
            LOGGER.warning(msg)
            largs.journal_format = "dotless"

        return largs

    @override
    def write(self, entries: list[Entry]) -> None:
        LOGGER.debug("Starting BibTeX export.")

        self.exported_entries = entries

        Event.PreBibtexExport.fire(self)

        journal_format = config.exporters.bibtex.journal_format
        if self.largs.journal_format is not None:
            journal_format = next(j for j in JournalFormat if j.value == self.largs.journal_format)
        LOGGER.debug("The journal field will be formatted as %s", journal_format.name)

        bibtex_parser = BibtexParser()

        for entry in self.exported_entries:
            LOGGER.info('Exporting entry "%s".', entry.label)
            if journal_format != JournalFormat.FULL:
                entry.data["journal"] = JournalAbbreviations.abbreviate(
                    entry.data["journal"], dotless=(journal_format == JournalFormat.DOTLESS)
                )
            entry_str = bibtex_parser.dump(entry)
            self.largs.file.write(entry_str)

        Event.PostBibtexExport.fire(self)

        self.largs.file.close()
