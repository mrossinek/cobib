"""CoBib show command"""

import argparse
import sys

from .base_command import Command


class ShowCommand(Command):  # pylint: disable=too-few-public-methods
    """Show Command"""

    name = 'show'

    def execute(self, args, out=sys.stdout):  # pylint: disable=arguments-differ
        """show entry

        Prints the details of a selected entry in bibtex format to stdout.
        """
        parser = argparse.ArgumentParser(prog="show", description="Show subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)
        largs = parser.parse_args(args)
        bib_data = self._read_database()
        try:
            entry = bib_data[largs.label]
            entry_str = entry.to_bibtex()
            print(entry_str, file=out)
        except KeyError:
            print("Error: No entry with the label '{}' could be found.".format(largs.label))
