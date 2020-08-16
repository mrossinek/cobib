"""CoBib delete command."""

import argparse
import logging
import os
import sys

from cobib.config import CONFIG
from cobib.database import read_database
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class DeleteCommand(Command):
    """Delete Command."""

    name = 'delete'

    def execute(self, args, out=sys.stdout):
        """Delete entry.

        Deletes the entry from the database.

        Args: See base class.
        """
        LOGGER.debug('Starting Delete command.')
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
                LOGGER.debug('Entry "%s" found. Starting to remove lines.', largs.label)
                entry_to_be_deleted = True
                buffer.pop()
                continue
            if entry_to_be_deleted and line.startswith('...'):
                LOGGER.debug('Reached end of entry "%s".', largs.label)
                entry_to_be_deleted = False
                continue
            if not entry_to_be_deleted:
                buffer.append(line)
        with open(file, 'w') as bib:
            for line in buffer:
                bib.write(line)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Delete command triggered from TUI.')
        # get current label
        label, _ = tui.get_current_label()
        # delete selected entry
        DeleteCommand().execute([label])
        # update database list
        LOGGER.debug('Updating list after Delete command.')
        read_database(fresh=True)
        tui.update_list()
        # if cursor line is below buffer height, move it one line back up
        if tui.current_line >= tui.buffer.height:
            tui.current_line -= 1
