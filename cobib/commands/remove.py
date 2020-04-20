"""CoBib remove command"""

import argparse
import os
import sys

from cobib.config import CONFIG
from .base_command import Command


class RemoveCommand(Command):  # pylint: disable=too-few-public-methods
    """Remove Command"""

    name = 'remove'

    def execute(self, args):
        """remove entry

        Removes the entry from the database.
        """
        parser = argparse.ArgumentParser(prog="remove", description="Remove subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)
        largs = parser.parse_args(args)
        conf_database = dict(CONFIG['DATABASE'])
        file = os.path.expanduser(conf_database['file'])
        with open(file, 'r') as bib:
            lines = bib.readlines()
        entry_to_be_removed = False
        buffer = []
        for line in lines:
            if line.startswith(largs.label):
                entry_to_be_removed = True
                buffer.pop()
                continue
            if entry_to_be_removed and line.startswith('...'):
                entry_to_be_removed = False
                continue
            if not entry_to_be_removed:
                buffer.append(line)
        with open(file, 'w') as bib:
            for line in buffer:
                bib.write(line)
