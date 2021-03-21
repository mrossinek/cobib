"""coBib modify command."""

import argparse
import logging
import os
import sys

from cobib.database import Database

from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)


class ModifyCommand(Command):
    """Modify Command."""

    name = "modify"

    @staticmethod
    def field_value_pair(string):
        """Utility method to assert the field-value pair argument type.

        Args:
            string (str): the argument string to check.
        """
        # try splitting the string into field and value, any errors will be handled by argparse
        field, value = string.split(":")
        return (field, value)

    def execute(self, args, out=sys.stdout):
        """Modify entries.

        Allows bulk modification of entries.

        Args: See base class.
        """
        LOGGER.debug("Starting Modify command.")
        parser = ArgumentParser(prog="modify", description="Modify subcommand parser.")
        parser.add_argument(
            "modification",
            type=self.field_value_pair,
            help="Modification to apply to the specified entries."
            "\nThis argument must be a string formatted as <field>:<value> where field can be any "
            "field of the entries and value can be any string which should be placed in that "
            "field. Be sure to escape this field-value pair properly, especially if the value "
            "contains spaces.",
        )
        parser.add_argument(
            "-a",
            "--append",
            action="store_true",
            help="Appends to the modified field rather than overwriting it.",
        )
        parser.add_argument(
            "-s",
            "--selection",
            action="store_true",
            help="When specified, the `filter` argument will be interpreted as a list of entry "
            "labels rather than arguments for the `list` command.",
        )
        parser.add_argument(
            "filter",
            nargs="+",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be modified. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            print(exc.message, file=sys.stderr)
            return

        out = open(os.devnull, "w")
        if largs.selection:
            LOGGER.info("Selection given. Interpreting `filter` as a list of labels")
            labels = largs.filter
        else:
            LOGGER.debug("Gathering filtered list of entries to be modified.")
            labels = ListCommand().execute(largs.filter, out=out)

        field, value = largs.modification

        if largs.append:
            msg = "The append-mode of the `modify` command has not been implemented yet."
            print(msg)
            LOGGER.warning(msg)
            sys.exit(1)

        bib = Database()

        for label in labels:
            try:
                entry = bib[label]
                entry.data[field] = value

                bib.update({label: entry})

                msg = f"'{label}' was modified."
                print(msg)
                LOGGER.info(msg)
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                print(msg)
                LOGGER.warning(msg)

        bib.save()

        self.git(args=vars(largs))

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug("Modify command triggered from TUI.")
        # handle input via prompt
        if tui.selection:
            tui.execute_command("modify -s", pass_selection=True)
        else:
            tui.execute_command("modify")
