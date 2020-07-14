"""CoBib open command."""

import argparse
import sys
from subprocess import Popen

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command


class OpenCommand(Command):
    """Open Command."""

    name = 'open'

    def execute(self, args, out=sys.stdout):
        """Open file from entry.

        Opens the associated file of an entry with xdg-open.

        Args: See base class.
        """
        parser = ArgumentParser(prog="open", description="Open subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return None

        try:
            entry = CONFIG.config['BIB_DATA'][largs.label]
            if 'file' not in entry.data.keys() or entry.data['file'] is None:
                error = "Error: There is no file associated with this entry."
                if out is None:
                    # called from TUI
                    return error
                print(error, file=out)
                sys.exit(1)
            opener = None
            opener = CONFIG.config['DATABASE'].get('open')
            try:
                Popen([opener, entry.data['file']])
            except FileNotFoundError:
                pass
        except KeyError:
            print("Error: No entry with the label '{}' could be found.".format(largs.label))

        return None

    @staticmethod
    def tui(tui):
        """See base class."""
        # get current label
        label, _ = tui.get_current_label()
        # populate buffer with entry data
        error = OpenCommand().execute([label], out=None)
        if error:
            tui.prompt.addstr(0, 0, error)
            tui.prompt.refresh()
