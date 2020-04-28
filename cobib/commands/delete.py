"""CoBib delete command"""

import argparse
import os
import sys

from cobib.config import CONFIG
from cobib.database import read_database
from .base_command import ArgumentParser, Command


class DeleteCommand(Command):
    """Delete Command"""

    name = 'delete'

    def execute(self, args, out=sys.stdout):
        """delete entry

        Deletes the entry from the database.
        """
        parser = ArgumentParser(prog="delete", description="Delete subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        conf_database = CONFIG.config['DATABASE']
        file = os.path.expanduser(conf_database['file'])
        with open(file, 'r') as bib:
            lines = bib.readlines()
        entry_to_be_deleted = False
        buffer = []
        for line in lines:
            if line.startswith(largs.label):
                entry_to_be_deleted = True
                buffer.pop()
                continue
            if entry_to_be_deleted and line.startswith('...'):
                entry_to_be_deleted = False
                continue
            if not entry_to_be_deleted:
                buffer.append(line)
        with open(file, 'w') as bib:
            for line in buffer:
                bib.write(line)

    @staticmethod
    def tui(tui):
        """TUI command interface"""
        # get current label
        label = tui.get_current_label()
        # delete selected entry
        DeleteCommand().execute([label])
        # update bibliography data
        read_database(fresh=True)
        # update database list
        tui.update_list()
