"""CoBib open command"""

import argparse
import sys
from subprocess import Popen

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command


class OpenCommand(Command):
    """Open Command"""

    name = 'open'

    def execute(self, args, out=sys.stdout):
        """open file from entry

        Opens the associated file of an entry with xdg-open.
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
            try:
                Popen(["xdg-open", entry.data['file']], stdin=None, stdout=None, stderr=None,
                      close_fds=True, shell=False)
            except FileNotFoundError:
                try:
                    Popen(["open", entry.data['file']], stdin=None, stdout=None, stderr=None,
                          close_fds=True, shell=False)
                except FileNotFoundError:
                    pass
        except KeyError:
            print("Error: No entry with the label '{}' could be found.".format(largs.label))

        return None

    @staticmethod
    def tui(tui):
        """TUI command interface"""
        prev_list_mode = tui.list_mode
        # get current label
        label = tui.get_current_label()
        # restore previous list_mode
        tui.list_mode = prev_list_mode
        # populate buffer with entry data
        error = OpenCommand().execute([label], out=None)
        if error:
            tui.prompt.addstr(0, 0, error)
            tui.prompt.refresh()
