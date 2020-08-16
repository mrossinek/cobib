"""CoBib add command."""

import argparse
import logging
import os
import sys
from collections import OrderedDict

from cobib.database import read_database, write_database
from cobib.parser import Entry
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class AddCommand(Command):
    """Add Command."""

    name = 'add'

    def execute(self, args, out=sys.stdout):
        """Add new entry.

        Adds new entries to the database.

        Args: See base class.
        """
        LOGGER.debug('Starting Add command.')
        parser = ArgumentParser(prog="add", description="Add subcommand parser.")
        parser.add_argument("-l", "--label", type=str,
                            help="the label for the new database entry")
        parser.add_argument("-f", "--file", type=str,
                            help="a file associated with this entry")
        group_add = parser.add_mutually_exclusive_group()
        group_add.add_argument("-a", "--arxiv", type=str,
                               help="arXiv ID of the new references")
        group_add.add_argument("-b", "--bibtex", type=argparse.FileType('r'),
                               help="BibLaTeX bibliographic data")
        group_add.add_argument("-d", "--doi", type=str,
                               help="DOI of the new references")
        parser.add_argument("tags", nargs=argparse.REMAINDER)
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        new_entries = OrderedDict()

        if largs.bibtex is not None:
            LOGGER.debug("Adding entries from BibLaTeX '%s'.", largs.bibtex)
            new_entries = Entry.from_bibtex(largs.bibtex)
        if largs.arxiv is not None:
            LOGGER.debug("Adding entries from arXiv '%s'.", largs.arxiv)
            new_entries = Entry.from_arxiv(largs.arxiv)
        if largs.doi is not None:
            LOGGER.debug("Adding entries from DOI '%s'.", largs.doi)
            new_entries = Entry.from_doi(largs.doi)

        if largs.label is not None:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/parser.py
                value.set_label = largs.label
            new_entries = OrderedDict((largs.label, value) for value in new_entries.values())

        if largs.file is not None:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/parser.py
                value.set_file = largs.file

        if largs.tags != []:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/parser.py
                value.set_tags = largs.tags

        write_database(new_entries)

        for value in new_entries.values():
            msg = f"'{value.label}' was added to the database."
            print(msg)
            LOGGER.info(msg)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Add command triggered from TUI.')
        # temporarily disable prints to stdout
        original_stdout = sys.stdout
        LOGGER.debug('Redirecting stdout.')
        sys.stdout = open(os.devnull, 'w')
        # handle input via prompt
        tui.prompt_handler('add')
        # restore stdout
        sys.stdout.close()
        sys.stdout = original_stdout
        # update database list
        LOGGER.debug('Updating list after Add command.')
        read_database(fresh=True)
        tui.update_list()
