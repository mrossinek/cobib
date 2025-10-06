"""Export entries.

.. include:: ../man/cobib-export.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
from typing import Any, Callable, ClassVar

from typing_extensions import override

from cobib.config import Event
from cobib.database import Database, Entry
from cobib.exporters.base_exporter import Exporter
from cobib.utils.entry_points import entry_points

from .base_command import Command
from .list_ import ListCommand

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ExportCommand(Command):
    """The Export Command.

    This command can parse the following arguments:

        * `-s`, `--selection`: when specified, the positional arguments will *not* be
          interpreted as filters but rather as a direct list of entry labels. This can
          be used on the command-line but is mainly meant for the TUIs visual selection
          interface (hence the name).
        * in addition to the options above, a *mutually exclusive group* of keyword arguments for
          all available `cobib.exporters` are registered at runtime. Please check the output of
          `cobib export --help` for the exact list.
        * finally, this command takes **TWO** sets of positional arguments:
            1. the arguments forwarded to the chosen exporter. For more information check the
               `--help` output of that exporter (e.g. `cobib export --bibtex --help`).
            2. the `filters` to specify a subset of your database for exporting. For more
               information refer to `cobib.commands.list_`.
            * to differentiate these clearly from each other, you can use the `--` separator. Here
              are some examples:
                * `cobib export --bibtex tmp.bib`
                * `cobib export --bibtex tmp.bib -- ++year 2025`
                * `cobib export --bibtex -- tmp.bib --abbreviate`
                * `cobib export --bibtex -- tmp.bib --abbreviate -- ++year 2025`
    """

    name = "export"

    # NOTE: the Callable type is unable to express the complex signature of the Exporter class
    _avail_exporters: ClassVar[dict[str, Callable[[Any], Exporter]]] = {
        cls.name: cls.load() for (cls, _) in entry_points("cobib.exporters")
    }
    """The available exporters."""

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.exported_entries: list[Entry] = []
        """A list of `cobib.database.Entry` objects which were exported by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="export",
            description="Export subcommand parser.",
            epilog="Read cobib-export.1 for more help.",
        )
        parser.add_argument(
            "-s",
            "--selection",
            action="store_true",
            help="When specified, the `filter` argument will be interpreted as a list of entry "
            "labels rather than arguments for the `list` command.",
        )
        parser.add_argument(
            "exporter_arguments",
            nargs="*",
            help="You can pass additional arguments to the chosen exporter. To ensure this works as"
            " expected you should add the pseudo-argument '--' before the remaining arguments.",
        )
        parser.add_argument(
            "filter",
            nargs="*",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be exported. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )
        group_export = parser.add_mutually_exclusive_group(required=True)
        for name in sorted(cls._avail_exporters.keys()):
            try:
                group_export.add_argument(f"--{name}", action="store_true", help=f"{name} exporter")
            except argparse.ArgumentError:  # pragma: no cover
                # NOTE: we ignore coverage for the special handling around here because this is
                # tested via the dummy plugin unittests in the CI.
                continue  # pragma: no cover
        cls.argparser = parser

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        separated_args: list[list[str]] = [[]]
        for arg in args:
            if arg == "--":
                separated_args.append([])
                continue
            separated_args[-1].append(arg)

        largs = super()._parse_args(tuple(separated_args[0]))
        if len(separated_args) > 3:  # noqa: PLR2004
            raise argparse.ArgumentError(None, "Found an unexpected number of `--` separators.")

        if len(separated_args) == 3:  # noqa: PLR2004
            largs.exporter_arguments = separated_args[1]
            largs.filter = separated_args[2]
        elif len(separated_args) == 2:  # noqa: PLR2004
            if len(largs.exporter_arguments) == 0:
                largs.exporter_arguments = separated_args[1]
            else:
                largs.filter = separated_args[1]

        return largs

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Export command.")

        Event.PreExportCommand.fire(self)

        if self.largs.selection:
            LOGGER.info("Selection given. Interpreting `filter` as a list of labels")
            labels = self.largs.filter
            bib = Database()
            for label in labels:
                try:
                    self.exported_entries.append(bib[label])
                except KeyError:
                    msg = f"No entry with the label '{label}' could be found."
                    LOGGER.warning(msg)
        else:
            LOGGER.debug("Gathering filtered list of entries to be exported.")
            self.exported_entries, _ = ListCommand(*self.largs.filter).execute_dull()

        for name, cls in ExportCommand._avail_exporters.items():  # pragma: no branch
            enabled = getattr(self.largs, name, False)
            if not enabled:
                continue
            LOGGER.debug("Exporting entries to %s.", name)
            cls(*self.largs.exporter_arguments).write(self.exported_entries)
            break

        Event.PostExportCommand.fire(self)
