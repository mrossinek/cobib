"""coBib's Import command.

.. include:: ../man/cobib-import.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
from collections import OrderedDict
from typing import Any, Callable, ClassVar

from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.importers.base_importer import Importer
from cobib.utils.entry_points import entry_points
from cobib.utils.logging import HINT

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ImportCommand(Command):
    """The ImportCommand.

    This command can parse the following arguments:

        * `--skip-download`: skips the automatic download of attached files (like PDFs).
        * `--force-download`: forces the automatic download of attached files (like PDFs).
        * in addition to the options above, a *mutually exclusive group* of keyword arguments for
          all available `cobib.importers` are registered at runtime. Please check the output of
          `cobib import --help` for the exact list.
        * finally, you can add another set of positional arguments (preceded by `--`) which will be
          passed on to the chosen importer. For more details see for example
          `cobib import --bibtex -- --help`.
    """

    name = "import"

    # NOTE: the Callable type is unable to express the complex signature of the Importer class
    _avail_importers: ClassVar[dict[str, Callable[[Any], Importer]]] = {
        cls.name: cls.load() for (cls, _) in entry_points("cobib.importers")
    }
    """The available importers."""

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.new_entries: dict[str, Entry] = OrderedDict()
        """An `OrderedDict` mapping labels to `cobib.database.Entry` instances which were imported
        by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="import",
            description="Import subcommand parser.",
            epilog="Read cobib-import.1 and cobib-importers.7 for more help.",
        )
        skip_download_group = parser.add_mutually_exclusive_group()
        skip_download_group.add_argument(
            "--skip-download",
            action="store_true",
            default=None,
            help="skip the automatic download of encountered PDF attachments",
        )
        skip_download_group.add_argument(
            "--force-download",
            dest="skip_download",
            action="store_false",
            default=None,
            help="force the automatic download of encountered PDF attachments",
        )
        parser.add_argument(
            "importer_arguments",
            nargs="*",
            help="You can pass additional arguments to the chosen importer. To ensure this works as"
            " expected you should add the pseudo-argument '--' before the remaining arguments.",
        )
        group_import = parser.add_mutually_exclusive_group(required=True)
        for name in sorted(cls._avail_importers.keys()):
            try:
                group_import.add_argument(f"--{name}", action="store_true", help=f"{name} importer")
            except argparse.ArgumentError:  # pragma: no cover
                # NOTE: we ignore coverage for the special handling around here because this is
                # tested via the dummy plugin unittests in the CI.
                continue  # pragma: no cover
        cls.argparser = parser

    @override
    async def execute(self) -> None:  # type: ignore[override]
        LOGGER.debug("Starting Import command.")

        Event.PreImportCommand.fire(self)

        imported_entries: list[Entry] = []

        skip_download = config.commands.import_.skip_download
        if self.largs.skip_download is not None:
            skip_download = self.largs.skip_download
        LOGGER.info(
            "Associated files will%s be downloaded from the imported library.",
            "" if skip_download else " not",
        )

        for name, cls in ImportCommand._avail_importers.items():
            enabled = getattr(self.largs, name, False)
            if not enabled:
                continue
            LOGGER.debug("Importing entries from %s.", name)
            imported_entries = await cls(  # type: ignore[call-arg]
                *self.largs.importer_arguments, skip_download=skip_download
            ).fetch()
            break

        bib = Database()
        existing_labels = set(bib.keys())

        for entry in imported_entries:
            # check if label already exists
            if entry.label in existing_labels:
                msg = (
                    f"The label '{entry.label}' already exists. It will be disambiguated based on "
                    "the configuration option: config.database.format.label_suffix"
                )
                LOGGER.warning(msg)
                new_label = bib.disambiguate_label(entry.label, entry)
                if new_label == entry.label:
                    continue
                entry.label = new_label

            bib.update({entry.label: entry})
            existing_labels.add(entry.label)
            self.new_entries[entry.label] = entry

        Event.PostImportCommand.fire(self)
        bib.update(self.new_entries)

        LOGGER.log(HINT, "Imported %s entries into the database.", len(self.new_entries))

        bib.save()

        self.git()
