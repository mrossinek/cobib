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

.. note::
   Since this command adds new entries to the database, its outcome can be affected by your
   `cobib.config.config.DatabaseConfig` settings. In particular, pay attention to the
   `cobib.config.config.EntryStringifyConfig` settings which affect how entries are converted
   to/from strings. In particular, the following setting will affect how multiple files are split
   into a list of files:
   ```
   config.database.stringify.list_separator.file = ", "
   ```
   The above will separate file paths using `, ` but if you use a different separator (for example
   `;`) be sure to update this setting accordingly.

### Additional Options

Since v4.1.0 you can suppress the automatic download of attachments via the
`cobib.config.config.ImportCommandConfig.skip_download` setting. It defaults to `False` meaning that
the attachments will be downloaded
If you want to manually overwrite the configuration setting you can do so with the `--skip-download`
and `--force-download` arguments, respectively.
I.e. the following will **not** download attachments:
```
cobib import --skip-download --zotero
```
While the next command will always download attachments:
```
cobib import --force-download --zotero
```

The various importers may take even more command line arguments. Please check out their
documentation at `cobib.importers` for more details.

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
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
from collections import OrderedDict
from typing import Any, Callable, ClassVar

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib import importers
from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.importers.base_importer import Importer

from .base_command import ArgumentParser, Command

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
          `cobib import --zotero -- --help`.
    """

    name = "import"

    # NOTE: the Callable type is unable to express the complex signature of the Importer class
    _avail_importers: ClassVar[dict[str, Callable[[Any], Importer]]] = {
        cls.name: cls for _, cls in inspect.getmembers(importers) if inspect.isclass(cls)
    }
    """The available importers."""

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.new_entries: dict[str, Entry] = OrderedDict()
        """An `OrderedDict` mapping labels to `cobib.database.Entry` instances which were imported
        by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="import", description="Import subcommand parser.")
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
        group_import = parser.add_mutually_exclusive_group()
        for name in cls._avail_importers.keys():
            try:
                group_import.add_argument(f"--{name}", action="store_true", help=f"{name} importer")
            except argparse.ArgumentError:
                continue
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
                entry.label = new_label

            bib.update({entry.label: entry})
            existing_labels.add(entry.label)
            self.new_entries[entry.label] = entry

        Event.PostImportCommand.fire(self)
        bib.update(self.new_entries)

        bib.save()
