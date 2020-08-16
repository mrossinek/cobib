"""CoBib show command."""

import argparse
import logging
import sys

from cobib import __version__
from cobib.config import CONFIG
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class ShowCommand(Command):
    """Show Command."""

    name = 'show'

    def execute(self, args, out=sys.stdout):
        """Show entry.

        Prints the details of a selected entry in BibLaTex format to stdout.

        Args: See base class.
        """
        LOGGER.debug('Starting Show command.')
        parser = ArgumentParser(prog="show", description="Show subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        try:
            entry = CONFIG.config['BIB_DATA'][largs.label]
            entry_str = entry.to_bibtex()
            print(entry_str, file=out)
        except KeyError:
            msg = f"No entry with the label '{largs.label}' could be found."
            LOGGER.error(msg)
            print(msg, file=out)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Show command triggered from TUI.')
        # get current label
        label, cur_y = tui.get_current_label()
        # populate buffer with entry data
        LOGGER.debug('Clearing current buffer contents.')
        tui.buffer.clear()
        ShowCommand().execute([label], out=tui.buffer)
        tui.buffer.split()
        LOGGER.debug('Populating buffer with ShowCommand result.')
        tui.buffer.view(tui.viewport, tui.visible, tui.width-1)

        # reset current cursor position
        tui.top_line = 0
        tui.current_line = 0
        # update top statusbar
        tui.topstatus = "CoBib v{} - {}".format(__version__, label)
        tui.statusbar(tui.topbar, tui.topstatus)
        # enter show menu
        tui.list_mode = cur_y
        tui.inactive_commands = ['Add', 'Filter', 'Search', 'Show', 'Sort']
