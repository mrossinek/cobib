"""CoBib open command"""

import argparse
import sys
from subprocess import Popen

from .base_command import Command


class OpenCommand(Command):  # pylint: disable=too-few-public-methods
    """Open Command"""

    name = 'open'

    def execute(self, args):
        """open file from entry

        Opens the associated file of an entry with xdg-open.
        """
        parser = argparse.ArgumentParser(prog="open", description="Open subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)
        largs = parser.parse_args(args)
        bib_data = self._read_database()
        try:
            entry = bib_data[largs.label]
            if 'file' not in entry.data.keys() or entry.data['file'] is None:
                print("Error: There is no file associated with this entry.")
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
