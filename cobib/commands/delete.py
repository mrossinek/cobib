"""CoBib delete command."""

import argparse
import logging
import sys

from cobib.database import Database
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class DeleteCommand(Command):
    """Delete Command."""

    name = 'delete'

    def execute(self, args, out=sys.stdout):
        """Delete entries.

        Deletes the entries from the database.

        Args: See base class.
        """
        LOGGER.debug('Starting Delete command.')
        parser = ArgumentParser(prog="delete", description="Delete subcommand parser.")
        parser.add_argument("labels", type=str, nargs='+', help="labels of the entries")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            print(exc.message, file=sys.stderr)
            return

        deleted_entries = set()

        bib = Database()
        for label in largs.labels:
            try:
                LOGGER.debug("Attempting to delete entry '%s'.", label)
                bib.pop(label)
                deleted_entries.add(label)
            except KeyError:
                pass

        bib.save()

        self.git(args=vars(largs))

        for label in deleted_entries:
            msg = f"'{label}' was removed from the database."
            print(msg)
            LOGGER.info(msg)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Delete command triggered from TUI.')
        if tui.selection:
            # use selection for command
            labels = list(tui.selection)
            tui.selection.clear()
        else:
            # get current label
            label, _ = tui.viewport.get_current_label()
            labels = [label]
        # delete selected entry
        tui.execute_command(['delete'] + labels, skip_prompt=True)
        # update database list
        LOGGER.debug('Updating list after Delete command.')
        tui.viewport.update_list()
