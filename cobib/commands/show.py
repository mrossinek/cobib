"""CoBib show command."""

import argparse
import logging
import sys

from cobib import __version__
from cobib.config import config
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
            entry = config.bibliography[largs.label]
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
        label, cur_y = tui.viewport.get_current_label()
        # populate buffer with entry data
        LOGGER.debug('Clearing current buffer contents.')
        tui.viewport.clear()
        ShowCommand().execute([label], out=tui.viewport.buffer)
        tui.viewport.buffer.split()
        if label in tui.selection:
            LOGGER.debug('Current entry is selected. Applying highlighting.')
            tui.viewport.buffer.replace(0, label,
                                        config.get_ansi_color('selection') + label + '\x1b[0m')
        LOGGER.debug('Populating buffer with ShowCommand result.')
        tui.viewport.view(ansi_map=tui.ANSI_MAP)

        # reset current cursor position
        tui.STATE.top_line = 0
        tui.STATE.current_line = 0
        # update top statusbar
        tui.STATE.topstatus = "CoBib v{} - {}".format(__version__, label)
        tui.statusbar(tui.topbar, tui.STATE.topstatus)
        # enter show menu
        tui.STATE.mode = 'show'
        tui.STATE.previous = cur_y
        tui.STATE.inactive_commands = ['Add', 'Filter', 'Show', 'Sort']
