"""CoBib add command"""

import argparse
import sys
from collections import OrderedDict

from cobib.parser import Entry
from .base_command import Command


class AddCommand(Command):  # pylint: disable=too-few-public-methods
    """Add Command"""

    name = 'add'

    def execute(self, args):
        """add new entry

        Adds new entries to the database.
        """
        parser = argparse.ArgumentParser(prog="add", description="Add subcommand parser.")
        parser.add_argument("-l", "--label", type=str,
                            help="the label for the new database entry")
        parser.add_argument("-f", "--file", type=str,
                            help="a file associated with this entry")
        group_add = parser.add_mutually_exclusive_group()
        group_add.add_argument("-a", "--arxiv", type=str,
                               help="arXiv ID of the new references")
        group_add.add_argument("-b", "--bibtex", type=argparse.FileType('r'),
                               help="BibTeX bibliographic data")
        group_add.add_argument("-d", "--doi", type=str,
                               help="DOI of the new references")
        parser.add_argument("tags", nargs=argparse.REMAINDER)
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)
        largs = parser.parse_args(args)

        new_entries = OrderedDict()

        if largs.bibtex is not None:
            new_entries = Entry.from_bibtex(largs.bibtex)
        if largs.arxiv is not None:
            new_entries = Entry.from_arxiv(largs.arxiv)
        if largs.doi is not None:
            new_entries = Entry.from_doi(largs.doi)

        if largs.file is not None:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                value.set_file(largs.file)

        if largs.label is not None:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                value.set_label(largs.label)
            new_entries = OrderedDict((largs.label, value) for value in new_entries.values())

        if largs.tags != []:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                value.set_tags(largs.tags)

        self._write_database(new_entries)
