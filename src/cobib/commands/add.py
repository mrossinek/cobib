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

.. note::
   Since this command adds new entries to the database, its outcome can be affected by your
   `cobib.config.config.DatabaseConfig` settings. In particular, pay attention to the
   `cobib.config.config.EntryStringifyConfig` settings which affect how entries are converted
   to/from strings. In particular, the following setting will affect how multiple files are split
   into a list of files:
   ```
   config.database.stringify.list_separator.file = ", "
   ```
   The above will separate file paths using `, ` but if you use a different separator (for example
   `;`) be sure to update this setting accordingly.

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
via `cobib.config.config.FileDownloaderConfig.default_location`, but it can be changed at runtime
using the `--path` argument like so:
```
cobib add --path <some custom path> --arxiv <some arXiv ID>
```
Since v4.1.0 you can suppress the automatic download via the
`cobib.config.config.AddCommandConfig.skip_download` setting. It defaults to `False` meaning that
the download will be attempted.
If you want to manually overwrite the configuration setting you can do so with the `--skip-download`
and `--force-download` arguments, respectively.
I.e. the following will **not** attempt the automatic download:
```
cobib add --skip-download --arxiv <some arXiv ID>
```
While the next command will always attempt the automatic download:
```
cobib add --force-download --arxiv <some arXiv ID>
```

Since v4.0.0 coBib will ask you what to do when encountering a conflict at runtime. That means, when
a label already exists in your database, you have various choices how to handle it:

1. you can `keep` the existing entry and skip the addition of the new one.
   .. note::
      This is equivalent to the old `--skip-existing` argument (added in v3.3.0) which is now
      deprecated and will be removed in a future version.

2. you can `replace` the existing entry.

3. you can `update` the existing entry.
   ```
   cobib add --doi <some DOI> --disambiguation update --label <some existing label>```

   This will take the existing entry and combine it with all new information found in the freshly
   added entry. Existing fields will be overwritten. If you have an automatically downloaded file
   associated with this entry, that will also be overwritten.
   This feature is especially useful if you want to update an entry which you previously added from
   the arXiv with its newly published version.
   .. note::
      This is equivalent to the `--update` argument (added in v3.3.0) which is now deprecated and
      will be removed in a future version.

4. you can `disambiguate` the entries. This will be done based on the
   `cobib.config.config.DatabaseFormatConfig.label_suffix` setting. It defaults to appending `_a`,
   `_b`, etc. to the label in order to differentiate (disambiguate) it from the already existing
   one.

When running into such a case, coBib will generate a side-by-side comparison of the existing and new
entry and give you the choice of how to proceed. The default choice is to *cancel* the addition
(i.e. `keep`) in order to prevent data loss.

If you already know that you will run into this case, you can bypass the prompt via the
`--disambiguation` argument and provide the intended answer ahead of time, for example like so:
```
cobib add --doi <some DOI> --disambiguation replace --label <some existing label>
```

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `a` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:add <arguments go here>
```
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import ClassVar

from rich.console import Console
from rich.prompt import InvalidResponse, PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib import parsers
from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.parsers import BibtexParser
from cobib.parsers.base_parser import Parser
from cobib.utils.diff_renderer import Differ
from cobib.utils.file_downloader import FileDownloader
from cobib.utils.journal_abbreviations import JournalAbbreviations
from cobib.utils.prompt import Prompt

from .base_command import ArgumentParser, Command
from .edit import EditCommand
from .modify import evaluate_as_f_string

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class AddCommand(Command):
    """The Add Command.

    This command can parse the following arguments:

        * `-l`, `--label`: the label to give to the new entry.
        * `--disambiguation`: hard-codes the reply to be used if a disambiguation prompt would
          occur.
        * `-f`, `--file`: one or multiple files to associate with this entry. This data will be
          stored in the `cobib.database.Entry.file` property.
        * `-p`, `--path`: the path to store the downloaded associated file in. This can be used to
          overwrite the `cobib.config.config.FileDownloaderConfig.default_location`.
        * `--skip-download`: skips the automatic download of an associated file.
        * `--force-download`: forces the automatic download of an associated file.
        * `--skip-existing`: **DEPRECATED** use `--disambiguation keep` instead!
        * `-u`, `--update`: **DEPRECATED** use `--disambiguation update` instead!
        * in addition to the options above, a *mutually exclusive group* of keyword arguments for
          all available `cobib.parsers` are registered at runtime. Please check the output of
          `cobib add --help` for the exact list.
        * any *positional* arguments (i.e. those, not preceded by a keyword) are interpreted as tags
          and will be stored in the `cobib.database.Entry.tags` property.
    """

    name = "add"

    _avail_parsers: ClassVar[dict[str, Callable[[], Parser]]] = {
        cls.name: cls for _, cls in inspect.getmembers(parsers) if inspect.isclass(cls)
    }
    """The available parsers."""

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.new_entries: dict[str, Entry] = OrderedDict()
        """An `OrderedDict` mapping labels to `cobib.database.Entry` instances which were added by
        this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="add", description="Add subcommand parser.")
        parser.add_argument("-l", "--label", type=str, help="the label for the new database entry")
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            nargs="+",
            action="extend",
            help="files associated with this entry",
        )
        parser.add_argument("-p", "--path", type=str, help="the path for the downloaded file")
        parser.add_argument(
            "--disambiguation",
            type=str,
            choices=["keep", "replace", "update", "disambiguate"],
            help="the reply in case of a disambiguation prompt",
        )
        skip_download_group = parser.add_mutually_exclusive_group()
        skip_download_group.add_argument(
            "--skip-download",
            action="store_true",
            default=None,
            help="skip the automatic download of an associated file",
        )
        skip_download_group.add_argument(
            "--force-download",
            dest="skip_download",
            action="store_false",
            default=None,
            help="force the automatic download of an associated file",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="DEPRECATED: use '--disambiguation keep' instead!",
        )
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="DEPRECATED: use '--disambiguation update' instead!",
        )
        group_add = parser.add_mutually_exclusive_group()
        for name in cls._avail_parsers.keys():
            try:
                group_add.add_argument(
                    f"-{name[0]}", f"--{name}", type=str, help=f"{name} object identifier"
                )
            except argparse.ArgumentError:
                try:
                    group_add.add_argument(f"--{name}", type=str, help=f"{name} object identifier")
                except argparse.ArgumentError:
                    continue
        parser.add_argument(
            "tags",
            nargs=argparse.REMAINDER,
            help="A list of space-separated tags to associate with this entry."
            "\nYou can use quotes to specify tags with spaces in them.",
        )

        cls.argparser = parser

    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        largs = super()._parse_args(args)

        if largs.skip_existing:
            msg = (
                "The '--skip-existing' argument of the 'add' command is deprecated! "
                "Instead you should use '--disambiguation keep'."
            )
            LOGGER.warning(msg)
            largs.disambiguation = "keep"

        if largs.update:
            msg = (
                "The '--update' argument of the 'add' command is deprecated! "
                "Instead you should use '--disambiguation update'."
            )
            LOGGER.warning(msg)
            largs.disambiguation = "update"

        return largs

    @override
    async def execute(self) -> None:  # type: ignore[override]  # noqa: PLR0912
        LOGGER.debug("Starting Add command.")

        Event.PreAddCommand.fire(self)

        edit_entries = False
        for name, cls in AddCommand._avail_parsers.items():
            string = getattr(self.largs, name, None)
            if string is None:
                continue
            LOGGER.debug("Adding entries from %s: '%s'.", name, string)
            self.new_entries = cls().parse(string)
            break
        else:
            if self.largs.label is not None:
                LOGGER.warning(
                    "No input to parse. Creating new entry '%s' manually.", self.largs.label
                )
                self.new_entries = {
                    self.largs.label: Entry(
                        self.largs.label,
                        {"ENTRYTYPE": config.commands.edit.default_entry_type},
                    )
                }
                edit_entries = True
            else:
                msg = "Neither an input to parse nor a label for manual creation specified!"
                LOGGER.error(msg)
                return

        if self.largs.label is not None:
            assert len(self.new_entries.values()) == 1
            for value in self.new_entries.copy().values():
                # logging done by cobib/database/entry.py
                value.label = self.largs.label
            self.new_entries = OrderedDict(
                (self.largs.label, value) for value in self.new_entries.values()
            )
        else:
            formatted_entries = OrderedDict()
            for label, value in self.new_entries.items():
                formatted_label = evaluate_as_f_string(
                    config.database.format.label_default, {"label": label, **value.data.copy()}
                )
                value.label = formatted_label
                formatted_entries[formatted_label] = value
            self.new_entries = formatted_entries

        if self.largs.file is not None:
            assert len(self.new_entries.values()) == 1
            for value in self.new_entries.values():
                # logging done by cobib/database/entry.py
                value.file = self.largs.file

        if self.largs.tags != []:
            assert len(self.new_entries.values()) == 1
            for value in self.new_entries.values():
                # logging done by cobib/database/entry.py
                value.tags = self.largs.tags

        skip_download = config.commands.add.skip_download
        if self.largs.skip_download is not None:
            skip_download = self.largs.skip_download
        LOGGER.info("Automatic file download will%s be attempted.", " not" if skip_download else "")

        bib = Database()
        existing_labels = set(bib.keys())

        for lbl, entry in self.new_entries.copy().items():
            overwrite_file = False
            # check if label already exists
            if lbl in existing_labels:
                # if it does, we have multiple cases to differentiate:
                if edit_entries:
                    # the user tried to manually add an entry which already exists, point them to
                    # the edit command instead
                    msg = (
                        f"You tried to add the '{lbl}' entry manually, but it already exists, "
                        f"please use `cobib edit {lbl}` instead!"
                    )
                    LOGGER.warning(msg)
                    continue
                # in all other cases, we enter an interactive prompt to let the user decide how
                # to proceed
                msg = f"You tried to add a new entry '{lbl}' which already exists!"
                LOGGER.warning(msg)
                res = self.largs.disambiguation
                # if the user provided the reply at runtime using the --disambiguation argument, the
                # following condition is not met
                if res is None:
                    parser = BibtexParser()
                    left = parser.dump(bib[lbl])
                    right = parser.dump(entry)
                    diff = Differ(left, right)
                    diff.compute()
                    table = diff.render("bibtex")

                    prompt_text = "How would you like to handle this conflict?"
                    choices = ["keep", "replace", "update", "disambiguate", "help"]
                    default = "keep"

                    res = await Prompt.ask(
                        prompt_text,
                        choices=choices,
                        default=default,
                        pre_prompt_message=table,
                        process_response_wrapper=self._wrap_prompt_process_response,
                    )

                if res == "update":
                    msg = f"Updating the already existing entry '{lbl}' with the new data."
                    LOGGER.info(msg)
                    entry.merge(bib[lbl], ours=True)
                    overwrite_file = True
                elif res == "disambiguate":
                    msg = (
                        "The label will be disambiguated based on the configuration option: "
                        "config.database.format.label_suffix"
                    )
                    LOGGER.warning(msg)
                    new_label = bib.disambiguate_label(lbl, entry)
                    entry.label = new_label
                    self.new_entries[new_label] = entry
                    self.new_entries.pop(lbl)
                elif res == "replace":
                    msg = f"Overwriting the already existing entry '{lbl}' with the new data."
                    LOGGER.info(msg)
                elif res == "keep":
                    msg = f"Skipping addition of the already existing entry '{lbl}'."
                    LOGGER.info(msg)
                    self.new_entries.pop(lbl)
                    continue

            # download associated file (if requested)
            if "_download" in entry.data.keys():
                if skip_download:
                    entry.data.pop("_download")
                else:
                    task = asyncio.create_task(
                        FileDownloader().download(
                            entry.data.pop("_download"),
                            entry.label,
                            folder=self.largs.path,
                            overwrite=overwrite_file,
                        )
                    )
                    path = await task
                    if path is not None:
                        entry.file = str(path)  # type: ignore[assignment]
            # check journal abbreviation
            if "journal" in entry.data.keys():
                entry.data["journal"] = JournalAbbreviations.elongate(entry.data["journal"])

        Event.PostAddCommand.fire(self)

        bib.update(self.new_entries)
        if edit_entries:
            EditCommand(self.largs.label).execute()

        bib.save()

        self.git()

        for label in self.new_entries:
            msg = f"'{label}' was added to the database."
            LOGGER.log(35, msg)

    @staticmethod
    def _wrap_prompt_process_response(
        func: Callable[[PromptBase[PromptType], str], PromptType],
    ) -> Callable[[PromptBase[PromptType], str], PromptType]:
        """A method to wrap a `PromptBase.process_response` method.

        This method wraps a `PromptBase.process_response` method in order to handle a user's request
        for additional help.

        Args:
            func: the `PromptBase.process_response` method to be wrapped.

        Returns:
            The wrapped `PromptBase.process_response` method.
        """

        @override  # type: ignore[misc]
        @wraps(func)
        def process_response(prompt: PromptBase[PromptType], value: str) -> PromptType:
            return_value: PromptType = func(prompt, value)

            if return_value == "help":
                LOGGER.debug("User requested help.")
                raise InvalidResponse(
                    "[yellow]A conflict between an existing (left) and newly added entry (right) "
                    "occurred. These are your options:\n"
                    "  'keep' the existing entry and discard the new addition (default)\n"
                    "  'replace' the existing entry with the new one\n"
                    "  'update' the existing entry with the new data\n"
                    "  'disambiguate' the new entry from the existing one by adding a label suffix"
                )

            return return_value

        return process_response
