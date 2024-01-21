"""coBib's Export command.

You can use this command to export your database.
As of now only two output formats are available:
* BibLaTex files
* Zip archives

The use case of the former is obvious and can be achieved by the following:
```
cobib export --bibtex my_database.bib
```
The latter case will collect all associated files of your database in a single Zip archive:
```
cobib export --zip my_references.zip
```
This is an important feature because coBib (by design) allows you to spread associated files across
your entire file system.
With this command you can gather them in a neat package for sharing or transferring.

You can also limit the export to a subset of your database in one of two ways:

1. through filters:
   ```
   cobib export --bibtex my_private_database.bib -- ++tags private
   ```

2. through a custom selection (using `--selection` or the short-hand option `-s`)
   ```
   cobib export --selection --bibtex some_other_database.bib -- Label1 Label2
   ```

.. note::
   While this latter case is usable via the command-line interface it is more a side-effect of the
   TUI integration which provides a visual selection (defaults to the `v` key).
   The proper and arguably more useful case is the first case using filters.

Since v3.2.0, coBib supports automatic Journal abbreviations. After configuring them as explained in
`cobib.config.config.UtilsConfig.journal_abbreviations` you can leverage them during exporting like
so:
```
cobib export --abbreviate --bibtex my_database.bib
# or
cobib export --abbreviate --dotless --bibtex my_database.bib
```

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `x` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:export <arguments go here>
```

.. note::
   If you have already selected one or more entries, the `--selection` argument will automatically
   be added.
"""

from __future__ import annotations

import argparse
import logging
from zipfile import ZipFile

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib.config import Event
from cobib.database import Database, Entry
from cobib.parsers.bibtex import BibtexParser
from cobib.utils.journal_abbreviations import JournalAbbreviations
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command
from .list_ import ListCommand

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ExportCommand(Command):
    """The Export Command.

    This command can parse the following arguments:

        * `-b`, `--bibtex`: specifies a BibLaTex filename into which to export.
        * `-z`, `--zip`: specifies a Zip-filename into which to export associated files.
        * `-a`, `--abbreviate`: abbreviate the Journal names before exporting. See also
          `cobib.config.config.UtilsConfig.journal_abbreviations`.
        * `--dotless`: remove punctuation from the Journal abbreviations.
        * `-s`, `--selection`: when specified, the positional arguments will *not* be
          interpreted as filters but rather as a direct list of entry labels. This can
          be used on the command-line but is mainly meant for the TUIs visual selection
          interface (hence the name).
        * in addition to the above, you can add `filters` to specify a subset of your
          database for exporting. For more information refer to `cobib.commands.list_`.
    """

    name = "export"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.exported_entries: list[Entry] = []
        """A list of `cobib.database.Entry` objects which were exported by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="export", description="Export subcommand parser.")
        parser.add_argument(
            "-b", "--bibtex", type=argparse.FileType("a"), help="BibLaTeX output file"
        )
        parser.add_argument("-z", "--zip", type=argparse.FileType("a"), help="zip output file")
        parser.add_argument(
            "-s",
            "--selection",
            action="store_true",
            help="When specified, the `filter` argument will be interpreted as a list of entry "
            "labels rather than arguments for the `list` command.",
        )
        parser.add_argument(
            "filter",
            nargs="*",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be exported. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )
        parser.add_argument(
            "-a", "--abbreviate", action="store_true", help="Abbreviate journal names"
        )
        parser.add_argument(
            "--dotless", action="store_true", help="Remove punctuation from journal abbreviations"
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Export command.")

        Event.PreExportCommand.fire(self)

        if self.largs.bibtex is None and self.largs.zip is None:
            msg = "No output file specified!"
            LOGGER.error(msg)
            return
        if self.largs.zip is not None:
            self.largs.zip = ZipFile(self.largs.zip.name, "w")

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

        bibtex_parser = BibtexParser()

        for entry in self.exported_entries:
            LOGGER.info('Exporting entry "%s".', entry.label)
            if self.largs.bibtex is not None:
                if self.largs.abbreviate and "journal" in entry.data.keys():
                    entry.data["journal"] = JournalAbbreviations.abbreviate(
                        entry.data["journal"], dotless=self.largs.dotless
                    )
                entry_str = bibtex_parser.dump(entry)
                self.largs.bibtex.write(entry_str)
            if self.largs.zip is not None:
                if "file" in entry.data.keys() and entry.file is not None:
                    files = entry.file
                    if not isinstance(files, list):
                        files = [files]
                    for file in files:
                        path = RelPath(file).path
                        LOGGER.debug(
                            'Adding "%s" associated with "%s" to the zip file.', path, entry.label
                        )
                        self.largs.zip.write(path, path.name)

        Event.PostExportCommand.fire(self)

        if self.largs.bibtex is not None:
            self.largs.bibtex.close()
        if self.largs.zip is not None:
            self.largs.zip.close()
