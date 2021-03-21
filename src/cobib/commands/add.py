"""coBib add command."""

import argparse
import inspect
import logging
import sys
from collections import OrderedDict

from cobib import parsers
from cobib.config import config
from cobib.database import Database, Entry

from .base_command import ArgumentParser, Command
from .edit import EditCommand

LOGGER = logging.getLogger(__name__)


class AddCommand(Command):
    """Add Command."""

    name = "add"

    def execute(self, args, out=sys.stdout):
        """Add new entry.

        Adds new entries to the database.

        Args: See base class.
        """
        LOGGER.debug("Starting Add command.")
        parser = ArgumentParser(prog="add", description="Add subcommand parser.")
        parser.add_argument("-l", "--label", type=str, help="the label for the new database entry")
        file_action = "extend" if sys.version_info[1] >= 8 else "append"
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            nargs="+",
            action=file_action,
            help="files associated with this entry",
        )
        group_add = parser.add_mutually_exclusive_group()
        avail_parsers = {
            cls.name: cls for _, cls in inspect.getmembers(parsers) if inspect.isclass(cls)
        }
        for name in avail_parsers.keys():
            group_add.add_argument(
                f"-{name[0]}", f"--{name}", type=str, help=f"{name} object identfier"
            )
        parser.add_argument(
            "tags",
            nargs=argparse.REMAINDER,
            help="A list of space-separated tags to associate with this entry."
            "\nYou can use quotes to specify tags with spaces in them.",
        )
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            print(exc.message, file=sys.stderr)
            return

        new_entries = OrderedDict()

        edit_entries = False
        for name, cls in avail_parsers.items():
            string = getattr(largs, name, None)
            if string is None:
                continue
            LOGGER.debug("Adding entries from %s: '%s'.", name, string)
            new_entries = cls().parse(string)
            break
        else:
            if largs.label is not None:
                LOGGER.warning("No input to parse. Creating new entry '%s' manually.", largs.label)
                new_entries = {
                    largs.label: Entry(
                        largs.label,
                        {"ID": largs.label, "ENTRYTYPE": config.commands.edit.default_entry_type},
                    )
                }
                edit_entries = True
            else:
                msg = "Neither an input to parse nor a label for manual creation specified!"
                print(msg, file=sys.stderr)
                LOGGER.error(msg)
                return

        if largs.label is not None:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/database/entry.py
                value.label = largs.label
            new_entries = OrderedDict((largs.label, value) for value in new_entries.values())

        if largs.file is not None:
            if file_action == "append":
                # We need to flatten the potentially nested list.
                # pylint: disable=import-outside-toplevel
                from itertools import chain

                largs.file = list(chain.from_iterable(largs.file))
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/database/entry.py
                value.file = largs.file

        if largs.tags != []:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/database/entry.py
                value.tags = largs.tags

        bib = Database()

        if largs.label in bib.keys():
            msg = (
                f"You tried to add a new entry '{largs.label}' which already exists!"
                f"\nPlease use `cobib edit {largs.label}` instead!"
            )
            LOGGER.warning(msg)
            return

        bib.update(new_entries)

        if edit_entries:
            EditCommand().execute([largs.label])

        bib.save()

        self.git(args=vars(largs))

        for label in new_entries:
            msg = f"'{label}' was added to the database."
            print(msg)
            LOGGER.info(msg)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug("Add command triggered from TUI.")
        # handle input via prompt
        tui.execute_command("add")
        # update database list
        LOGGER.debug("Updating list after Add command.")
        tui.viewport.update_list()
