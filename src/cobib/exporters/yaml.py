"""coBib's YAML exporter.

.. include:: ../man/cobib-yaml.7.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from typing_extensions import override

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import YAMLParser

from .base_exporter import Exporter

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class YAMLExporter(Exporter):
    """The YAMLporter.

    This exporter can parse the following arguments:

        * `file`: the YAML file into which to export entries.
    """

    name = "yaml"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="yaml",
            description="YAML exporter.",
            epilog="Read cobib-yaml.7 for more help.",
        )
        parser.add_argument("file", type=str, help="the YAML file into which to export")

        cls.argparser = parser

    @override
    def write(self, entries: list[Entry]) -> None:
        LOGGER.debug("Starting YAML export.")

        self.exported_entries = entries

        self.largs.file = open(self.largs.file, "a")

        Event.PreYAMLExport.fire(self)

        yaml_parser = YAMLParser()

        for entry in self.exported_entries:
            LOGGER.info('Exporting entry "%s".', entry.label)
            entry_str = yaml_parser.dump(entry)
            self.largs.file.write(entry_str)

        Event.PostYAMLExport.fire(self)

        self.largs.file.close()
