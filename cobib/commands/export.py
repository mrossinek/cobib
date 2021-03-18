"""CoBib export command."""

import argparse
import logging
import os
import sys
from zipfile import ZipFile

from cobib.database import Database
from cobib.parsers import BibtexParser
from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)


class ExportCommand(Command):
    """Export Command."""

    name = 'export'

    def execute(self, args, out=sys.stdout):
        """Export database.

        Exports all entries matched by the filter queries (see the list docs).
        Currently supported exporting formats are:
        * BibLaTex databases
        * zip archives

        Args: See base class.
        """
        LOGGER.debug('Starting Export command.')
        parser = ArgumentParser(prog="export", description="Export subcommand parser.")
        parser.add_argument("-b", "--bibtex", type=argparse.FileType('a'),
                            help="BibLaTeX output file")
        parser.add_argument("-z", "--zip", type=argparse.FileType('a'),
                            help="zip output file")
        parser.add_argument("-s", "--selection", action="store_true",
                            help="When specified, the `filter` argument will be interpreted as "
                            "a list of entry labels rather than arguments for the `list` command.")
        parser.add_argument('filter', nargs='*',
                            help="You can specify filters as used by the `list` command in order "
                            "to select a subset of labels to be modified. To ensure this works as "
                            "expected you should add the pseudo-argument '--' before the list of "
                            "filters. See also `list --help` for more information.")

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
            largs.zip = ZipFile(largs.zip.name, 'w')
        out = open(os.devnull, 'w')
        if largs.selection:
            LOGGER.info('Selection given. Interpreting `filter` as a list of labels')
            labels = largs.filter
        else:
            LOGGER.debug('Gathering filtered list of entries to be exported.')
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
                    if 'file' in entry.data.keys() and entry.file is not None:
                        LOGGER.debug('Adding "%s" associated with "%s" to the zip file.',
                                     entry.file, label)
                        largs.zip.write(entry.file, os.path.basename(entry.file))
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                print(msg)
                LOGGER.warning(msg)

        if largs.zip is not None:
            largs.zip.close()

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Export command triggered from TUI.')
        # handle input via prompt
        if tui.selection:
            tui.execute_command('export -s', pass_selection=True)
        else:
            tui.execute_command('export')
