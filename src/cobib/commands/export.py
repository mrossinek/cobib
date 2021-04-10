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
2. through a custom selection (using `--selection`)
```
cobib export --selection --bibtex some_other_database.bib -- DummyID1 DummyID2
```
While this latter case is usable via the command-line interface it is more a side-effect of the TUI
integration which provides a visual selection (defaults to the `v` key).
The proper and arguably more useful case is the first case using filters.

You can also trigger this command from the `cobib.tui.TUI`.
By default, it is bound to the `x` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:export <arguments go here>
```
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import IO, TYPE_CHECKING, List
from zipfile import ZipFile

from cobib.database import Database
from cobib.parsers import BibtexParser

from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cobib.tui import TUI


class ExportCommand(Command):
    """The Export Command."""

    name = "export"

    def execute(self, args: List[str], out: IO = sys.stdout) -> None:
        """Exports the database.

        This command exports the database (or a selected subset of entries).
        You can choose the exported formats from the following list:
        * BibLaTex (via the `--bibtex` argument)
        * Zip archive (via the `--zip` argument)

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `-b`, `--bibtex`: specifies a BibLaTex filename into which to export.
                    * `-z`, `--zip`: specifies a Zip-filename into which to export associated files.
                    * `-s`, `--selection`: when specified, the positional arguments will *not* be
                      interpreted as filters but rather as a direct list of entry labels. This can
                      be used on the command-line but is mainly meant for the TUIs visual selection
                      interface (hence the name).
                    * in addition to the above, you can add `filters` to specify a subset of your
                      database for exporting. For more information refer to `cobib.commands.list`.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Export command.")
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
            "subset of labels to be modified. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            print(exc.message, file=sys.stderr)
            return

        if largs.bibtex is None and largs.zip is None:
            msg = "No output file specified!"
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return
        if largs.zip is not None:
            largs.zip = ZipFile(largs.zip.name, "w")
        out = open(os.devnull, "w")
        if largs.selection:
            LOGGER.info("Selection given. Interpreting `filter` as a list of labels")
            labels = largs.filter
        else:
            LOGGER.debug("Gathering filtered list of entries to be exported.")
            labels = ListCommand().execute(largs.filter, out=out)

        bibtex_parser = BibtexParser()

        bib = Database()

        for label in labels:
            try:
                LOGGER.info('Exporting entry "%s".', label)
                entry = bib[label]
                if largs.bibtex is not None:
                    entry_str = bibtex_parser.dump(entry)
                    largs.bibtex.write(entry_str)
                if largs.zip is not None:
                    if "file" in entry.data.keys() and entry.file is not None:
                        LOGGER.debug(
                            'Adding "%s" associated with "%s" to the zip file.', entry.file, label
                        )
                        largs.zip.write(entry.file, os.path.basename(entry.file))
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                print(msg)
                LOGGER.warning(msg)

        if largs.zip is not None:
            largs.zip.close()

    @staticmethod
    def tui(tui: TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Export command triggered from TUI.")
        # handle input via prompt
        if tui.selection:
            tui.execute_command("export -s", pass_selection=True)
        else:
            tui.execute_command("export")
