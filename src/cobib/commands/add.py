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
cobib add --url <some URL>
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
instead specify a new label like so:
```
cobib add --label <some new label>
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

Since v3.2.0 coBib attempts to download PDF files for newly added entries (if the corresponding
parser supports this feature). The default location where this file will be stored can be configured
via `config.utils.file_downloader.default_location`, but it can be changed at runtime using the
`--path` argument like so:
```
cobib add --path <some custom path> --arxiv <some arXiv ID>
```
If you want to manually suppress the automatic download, specify the `--skip-download` argument:
```
cobib add --skip-download --arxiv <some arXiv ID>
```

Since v3.3.0 you can also update existing entries by using the `--update` argument:
```
cobib add --doi <some DOI> --update --label <some existing label>
```
This will take the existing entry and combine it with all new information found in the freshly added
entry. Existing fields will be overwritten. If you have an automatically downloaded file associated
with this entry, that will also be overwritten.
This feature is especially useful if you want to update an entry which you previously added from the
arXiv with its newly published version.

If you don't specify `--update` and run into a situation where the label which you are trying to add
already exists, coBib will disambiguate it based on the `config.database.format.label_suffix`
setting. It defaults to appending `_a`, `_b`, etc.
You can disable this disambiguation by passing `--skip-existing` to the add command.

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
from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.utils.file_downloader import FileDownloader
from cobib.utils.journal_abbreviations import JournalAbbreviations

from .base_command import ArgumentParser, Command
from .edit import EditCommand
from .modify import evaluate_as_f_string

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class AddCommand(Command):
    """The Add Command."""

    name = "add"

    # pylint: disable=too-many-branches,too-many-statements
    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Adds a new entry.

        Depending on the `args`, if a keyword for one of the available `cobib.parsers` was used
        together with a matching input, that parser will be used to create the new entry.
        Otherwise, the command is only valid if the `--label` option was used to specify a new entry
        label, in which case this command will trigger the `cobib.commands.edit.EditCommand` for a
        manual entry addition.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `-l`, `--label`: the label to give to the new entry.
                    * `-u`, `--update`: updates an existing database entry if it already exists.
                    * `-f`, `--file`: one or multiple files to associate with this entry. This data
                      will be stored in the `cobib.database.Entry.file` property.
                    * `-p`, `--path`: the path to store the downloaded associated file in. This can
                      be used to overwrite the `config.utils.file_downloader.default_location`.
                    * `--skip-download`: skips the automatic download of an associated file.
                    * `--skip-existing`: skips entry if label exists instead of running label
                      disambiguation.
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
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="update an entry if the label exists already",
        )
        file_action = "extend" if sys.version_info[1] >= 8 else "append"
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            nargs="+",
            action=file_action,
            help="files associated with this entry",
        )
        parser.add_argument("-p", "--path", type=str, help="the path for the associated file")
        parser.add_argument(
            "--skip-download",
            action="store_true",
            help="skip the automatic download of an associated file",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="skips entry addition if existent instead of using label disambiguation",
        )
        group_add = parser.add_mutually_exclusive_group()
        avail_parsers = {
            cls.name: cls for _, cls in inspect.getmembers(parsers) if inspect.isclass(cls)
        }
        for name in avail_parsers.keys():
            try:
                group_add.add_argument(
                    f"-{name[0]}", f"--{name}", type=str, help=f"{name} object identfier"
                )
            except argparse.ArgumentError:
                try:
                    group_add.add_argument(f"--{name}", type=str, help=f"{name} object identfier")
                except argparse.ArgumentError:
                    continue
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
            return

        Event.PreAddCommand.fire(largs)

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
                LOGGER.error(msg)
                return

        if largs.label is not None:
            assert len(new_entries.values()) == 1
            for value in new_entries.values():
                # logging done by cobib/database/entry.py
                value.label = largs.label
            new_entries = OrderedDict((largs.label, value) for value in new_entries.values())
        else:
            formatted_entries = OrderedDict()
            for label, value in new_entries.items():
                formatted_label = evaluate_as_f_string(
                    config.database.format.label_default, {"label": label, **value.data.copy()}
                )
                value.label = formatted_label
                formatted_entries[formatted_label] = value
            new_entries = formatted_entries

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
        existing_labels = set(bib.keys())

        for lbl, entry in new_entries.copy().items():
            # check if label already exists
            if lbl in existing_labels:
                if not largs.update:
                    msg = f"You tried to add a new entry '{lbl}' which already exists!"
                    LOGGER.warning(msg)
                    if edit_entries or largs.skip_existing:
                        msg = f"Please use `cobib edit {lbl}` instead!"
                        LOGGER.warning(msg)
                        continue
                    msg = (
                        "The label will be disambiguated based on the configuration option: "
                        "config.database.format.label_suffix"
                    )
                    LOGGER.warning(msg)
                    new_label = bib.disambiguate_label(lbl)
                    entry.label = new_label
                    new_entries[new_label] = entry
                    new_entries.pop(lbl)
                else:
                    # label exists but the user asked to update an existing entry
                    existing_data = bib[lbl].data.copy()
                    existing_data.update(entry.data)
                    entry.data = existing_data.copy()
            # download associated file (if requested)
            if "_download" in entry.data.keys():
                if largs.skip_download:
                    entry.data.pop("_download")
                else:
                    path = FileDownloader().download(
                        entry.data.pop("_download"), lbl, folder=largs.path, overwrite=largs.update
                    )
                    if path is not None:
                        entry.data["file"] = str(path)
            # check journal abbreviation
            if "journal" in entry.data.keys():
                entry.data["journal"] = JournalAbbreviations.elongate(entry.data["journal"])

        Event.PostAddCommand.fire(new_entries)

        bib.update(new_entries)
        if edit_entries:
            EditCommand().execute([largs.label])

        bib.save()

        self.git(args=vars(largs))

        for label in new_entries:
            msg = f"'{label}' was added to the database."
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
