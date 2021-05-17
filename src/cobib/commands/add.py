"""coBib's Add command.

This command allows you to add new entries to your database.
You have two options on how to use this command.

### 1. Parser-based addition

All parsers available in `cobib.parsers` will be registered (at runtime) in a *mutually exclusive*
group of keyword arguments.
This means, that you can add a new entry based on any of them by using the keyword argument
according to the parsers name.
For example:
```
cobib add --bibtex some_biblatex_file.bib
cobib add --arxiv <some arXiv ID>
cobib add --doi <some DOI>
cobib add --isbn <some ISBN>
cobib add --yaml some_cobib_style_yaml_file.yaml
```

Note, that you cannot combine multiple parsers within a single command execution (for obvious
reasons).

Furthermore, most of these parsers will set the entry label automatically.
If you would like to prevent that and specify a custom label directly, you can add the `--label`
keyword argument to your command like so:
```
cobib add --doi <some DOI> --label "MyLabel"
```

### 2. Manual entry addition

If you want to add a new entry manually, you *must* omit any of the parser keyword arguments and
instead specify a new label ID like so:
```
cobib add --label <some new label ID>
```
This will trigger the `cobib.commands.edit.EditCommand` for a manual addition.
However, the benefit of using this through the `AddCommand` is the availability of the following
additional options which are always available (i.e. also in combination with the parser keyword
arguments, above).

### Additional Options

You can directly associate your new entry with one or multiple files by doing the following:
```
cobib add --doi <some DOI> --file /path/to/a/file.pdf [/path/to/another/file.dat ...]
```

You can also specify `cobib.database.Entry.tags` using *positional* arguments like so:
```
cobib add --doi <some DOI> -- tag1 "multi-word tag2" ...
```

### TUI

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `a` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:add <arguments go here>
```
"""

from __future__ import annotations

import argparse
import inspect
import logging
import sys
from collections import OrderedDict
from typing import IO, TYPE_CHECKING, Any, Dict, List

from cobib import parsers
from cobib.config import config
from cobib.database import Database, Entry

from .base_command import ArgumentParser, Command
from .edit import EditCommand

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class AddCommand(Command):
    """The Add Command."""

    name = "add"

    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Adds a new entry.

        Depending on the `args`, if a keyword for one of the available `cobib.parsers` was used
        together with a matching input, that parser will be used to create the new entry.
        Otherwise, the command is only valid if the `--label` option was used to specify a new entry
        ID, in which case this command will trigger the `cobib.commands.edit.EditCommand` for a
        manual entry addition.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `-l`, `--label`: the ID to give to the new entry.
                    * `-f`, `--file`: one or multiple files to associate with this entry. This data
                      will be stored in the `cobib.database.Entry.file` property.
                    * in addition to the options above, a *mutually exclusive group* of keyword
                      arguments for all available `cobib.parsers` are registered at runtime. Please
                      check the output of `cobib add --help` for the exact list.
                    * any *positional* arguments (i.e. those, not preceded by a keyword) are
                      interpreted as tags and will be stored in the `cobib.database.Entry.tags`
                      property.
            out: the output IO stream. This defaults to `sys.stdout`.
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

        new_entries: Dict[str, Entry] = OrderedDict()

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
                        {"ENTRYTYPE": config.commands.edit.default_entry_type},
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
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Add command triggered from TUI.")
        # handle input via prompt
        tui.execute_command("add")
        # update database list
        LOGGER.debug("Updating list after Add command.")
        tui.viewport.update_list()
