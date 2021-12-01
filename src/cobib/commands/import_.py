"""coBib's Import command.

This command allows you to import new entries from another bibliography manager into coBib.
This can be seen as a migration utility and, thus, you are likely to only execute this command once.
To ease the interface (and implementation), this process of adding new entries to your database is
separated from the `cobib.commands.add.AddCommand`.

To support various bibliography managers as sources for this command, their code is split out into a
separate module, `cobib.importers`.
The various backends are registered (at runtime) in a *mutually exclusive* group of keyword
arguments, which you can use like so:
```
cobib import --zotero
```

### Additional Options

If you want to suppress the automatic download of attachments, specify the `--skip-download`
argument like so:
```
cobib import --skip-download --zotero
```

The various importers may take even more command line arguments. Please check out their
documentation at `cobib.importers` for more details.

### TUI

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `i` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:import <arguments go here>
```
"""

from __future__ import annotations

import argparse
import inspect
import logging
import sys
from collections import OrderedDict
from typing import IO, TYPE_CHECKING, Any, Dict, List

from cobib import importers
from cobib.config import Event
from cobib.database import Database, Entry

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class ImportCommand(Command):
    """The ImportCommand."""

    name = "import"

    # pylint: disable=too-many-branches,too-many-statements
    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Imports new entries from another bibliography manager.

        The source from which to import new entries is configured via the `args`. The available
        importers are provided by the `cobib.importers` module.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `--skip-download`: skips the automatic download of attached files (like PDFs).
                    * in addition to the options above, a *mutually exclusive group* of keyword
                      arguments for all available `cobib.importers` are registered at runtime.
                      Please check the output of `cobib import --help` for the exact list.
                    * finally, you can add another set of positional arguments (preceded by `--`)
                      which will be passed on to the chosen importer. For more details see for
                      example `cobib import --zotero -- --help`.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Import command.")
        parser = ArgumentParser(prog="import", description="Import subcommand parser.")
        parser.add_argument(
            "--skip-download",
            action="store_true",
            help="skip the automatic download of encountered PDF attachments",
        )
        parser.add_argument(
            "importer_arguments",
            nargs="*",
            help="You can pass additional arguments to the chosen importer. To ensure this works as"
            " expected you should add the pseudo-argument '--' before the remaining arguments.",
        )
        group_import = parser.add_mutually_exclusive_group()
        avail_parsers = {
            cls.name: cls for _, cls in inspect.getmembers(importers) if inspect.isclass(cls)
        }
        for name in avail_parsers.keys():
            try:
                group_import.add_argument(f"--{name}", action="store_true", help=f"{name} importer")
            except argparse.ArgumentError:
                continue

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return

        Event.PreImportCommand.fire(largs)

        imported_entries: List[Entry] = []

        for name, cls in avail_parsers.items():
            enabled = getattr(largs, name, False)
            if not enabled:
                continue
            LOGGER.debug("Importing entries from %s.", name)
            imported_entries = cls().fetch(
                largs.importer_arguments, skip_download=largs.skip_download
            )
            break

        bib = Database()
        existing_labels = set(bib.keys())

        new_entries: Dict[str, Entry] = OrderedDict()

        for entry in imported_entries:
            # check if label already exists
            if entry.label in existing_labels:
                msg = (
                    f"The label '{entry.label}' already exists. It will be disambiguated based on "
                    "the configuration option: config.database.format.label_suffix"
                )
                LOGGER.warning(msg)
                new_label = bib.disambiguate_label(entry.label, entry)
                entry.label = new_label

            bib.update({entry.label: entry})
            existing_labels.add(entry.label)
            new_entries[entry.label] = entry

        Event.PostImportCommand.fire(new_entries)
        bib.update(new_entries)

        bib.save()

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Import command triggered from TUI.")
        # handle input via prompt
        tui.execute_command("import")
        # update database list
        LOGGER.debug("Updating list after Import command.")
        tui.viewport.update_list()
