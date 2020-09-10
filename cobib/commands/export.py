"""CoBib export command."""

import argparse
import logging
import os
import sys
from zipfile import ZipFile

from cobib.config import CONFIG
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
        parser.add_argument('list_arg', nargs='*',
                            help="Any arguments for the List subcommand." +
                            "\nUse this to add filters to specify a subset of exported entries." +
                            "\nYou can add a '--' before the List arguments to ensure separation." +
                            "\nSee also `list --help` for more information on the List arguments.")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        if largs.bibtex is None and largs.zip is None:
            msg = "No output file specified!"
            print("Error: " + msg, file=sys.stderr)
            LOGGER.error(msg)
            return
        if largs.zip is not None:
            largs.zip = ZipFile(largs.zip.name, 'w')
        out = open(os.devnull, 'w')
        LOGGER.debug('Gathering filtered list of entries to be exported.')
        labels = ListCommand().execute(largs.list_arg, out=out)

        try:
            for label in labels:
                LOGGER.debug('Exporting entry "%s".', label)
                entry = CONFIG.config['BIB_DATA'][label]
                if largs.bibtex is not None:
                    entry_str = entry.to_bibtex()
                    largs.bibtex.write(entry_str)
                if largs.zip is not None:
                    if 'file' in entry.data.keys() and entry.data['file'] is not None:
                        LOGGER.debug('Adding "%s" associated with "%s" to the zip file.',
                                     entry.data['file'], label)
                        largs.zip.write(entry.data['file'], label+'.pdf')
        except KeyError:
            print("Error: No entry with the label '{}' could be found.".format(largs.label))

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Export command triggered from TUI.')
        # handle input via prompt
        tui.prompt_handler('export')
