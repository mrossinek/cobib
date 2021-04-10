"""coBib's Modify command.

This command allows you to perform bulk modification to multiple entries.
Thus, it provides faster means to apply simple edits to many entries at once, without having to open
each entry for editing one-by-one or having to edit the database file manually.

A simple example is the following:
```
cobib modify tags:private --selection -- DummyID1 DummyID2 ...
```
which will set the tags of all listed entries to `private`.

In the future, we plan to support an `--append` option which will allow appending to existing values
of a field rather than simply overwriting all previous contents.

As with other commands, you can also use filters (see also `cobib.commands.list`) rather than a
manual selection to specify the entries which to modify:
```
cobib modify tags:first_author -- ++author Rossmannek
```

You can also trigger this command from the `cobib.tui.TUI`.
By default, it is bound to the `m` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:modify <arguments go here>
```
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import IO, TYPE_CHECKING, List, Tuple

from cobib.database import Database

from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cobib.tui import TUI


class ModifyCommand(Command):
    """The Modify Command."""

    name = "modify"

    @staticmethod
    def field_value_pair(string: str) -> Tuple[str, str]:
        """Utility method to assert the field-value pair argument type.

        This method is given to the `argparse.ArgumentParser` instance as its `type` specifier.
        An input argument is considered valid if it passes through this function without raising any
        errors, which means it conforms to the `<field>:<value>` notation.

        Args:
            string: the argument string to check.
        """
        # try splitting the string into field and value, any errors will be handled by argparse
        field, value = string.split(":")
        return (field, value)

    def execute(self, args: List[str], out: IO = sys.stdout) -> None:
        """Modifies multiple entries in bulk.

        This command allows bulk modification of multiple entries.
        It takes a modification in the form `<field>:<value>` and will overwrite the `field` of all
        matching entries with the new `value`.
        The entries can be specified as a manual selection (when using `--selection` or the visual
        selection of the TUI) or through filters (see also `cobib.commands.list`).

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `modification`: a string conforming to `<field>:<value>` indicating the
                      modification that should be applied to all matching entries. By default, the
                      modification will overwrite any existing data in the specified `field` with
                      the new `value`.
                    * `-a`, `--append`: **TO BE IMPLEMENTED**.
                    * `-s`, `--selection`: when specified, the positional arguments will *not* be
                      interpreted as filters but rather as a direct list of entry labels. This can
                      be used on the command-line but is mainly meant for the TUIs visual selection
                      interface (hence the name).
                    * in addition to the above, you can add `filters` to specify a subset of your
                      database for exporting. For more information refer to `cobib.commands.list`.
            out: the output IO stream. This defaults to `sys.stdout`.
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
    def tui(tui: TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Modify command triggered from TUI.")
        # handle input via prompt
        if tui.selection:
            tui.execute_command("modify -s", pass_selection=True)
        else:
            tui.execute_command("modify")
