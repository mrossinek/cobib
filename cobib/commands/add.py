"""CoBib add command."""

import argparse
import logging
import sys
from collections import OrderedDict

from cobib.config import CONFIG
from cobib.database import read_database, write_database
from cobib.parser import Entry
from .base_command import ArgumentParser, Command
from .edit import EditCommand

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
        parser.add_argument("-f", "--file", type=str, nargs="+", action="extend",
                            help="files associated with this entry")
        group_add = parser.add_mutually_exclusive_group()
        group_add.add_argument("-a", "--arxiv", type=str,
                               help="arXiv ID of the new references")
        group_add.add_argument("-b", "--bibtex", type=argparse.FileType('r'),
                               help="BibLaTeX bibliographic data")
        group_add.add_argument("-d", "--doi", type=str,
                               help="DOI of the new references")
        group_add.add_argument("-i", "--isbn", type=str,
                               help="ISBN of the new references")
        parser.add_argument("tags", nargs=argparse.REMAINDER,
                            help="A list of space-separated tags to associate with this entry." +
                            "\nYou can use quotes to specify tags with spaces in them.")
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        new_entries = OrderedDict()

        edit_entries = False
        if largs.bibtex is not None:
            LOGGER.debug("Adding entries from BibLaTeX '%s'.", largs.bibtex)
            new_entries = Entry.from_bibtex(largs.bibtex)
        elif largs.arxiv is not None:
            LOGGER.debug("Adding entries from arXiv '%s'.", largs.arxiv)
            new_entries = Entry.from_arxiv(largs.arxiv)
        elif largs.doi is not None:
            LOGGER.debug("Adding entries from DOI '%s'.", largs.doi)
            new_entries = Entry.from_doi(largs.doi)
        elif largs.isbn is not None:
            LOGGER.debug("Adding entries from ISBN '%s'.", largs.isbn)
            new_entries = Entry.from_isbn(largs.isbn)
        elif largs.label is not None:
            LOGGER.warning("No input to parse. Creating new entry '%s' manually.", largs.label)
            new_entries = {
                largs.label: Entry(largs.label,
                                   {'ID': largs.label,
                                    'ENTRYTYPE': CONFIG.config['FORMAT']['default_entry_type']})
                }
            edit_entries = True
        else:
            LOGGER.error("Neither an input to parse nor a label for manual creation specified!")
            return

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

        # Write the new entries to the database. This destructively overwrite the variable with a
        # list of labels of the entries which have actually been added to the database.
        new_entries = write_database(new_entries)

        if edit_entries:
            if largs.label not in new_entries:
                msg = f"You tried to add a new entry '{largs.label}' which already exists!\n" \
                    + f"Please use `cobib edit {largs.label}` instead!"
                LOGGER.warning(msg)
            else:
                read_database(fresh=True)
                EditCommand().execute([largs.label])

        self.git(args=vars(largs))

        for label in new_entries:
            msg = f"'{label}' was added to the database."
            print(msg)
            LOGGER.info(msg)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Add command triggered from TUI.')
        # handle input via prompt
        tui.execute_command('add')
        # update database list
        LOGGER.debug('Updating list after Add command.')
        read_database(fresh=True)
        tui.viewport.update_list()
