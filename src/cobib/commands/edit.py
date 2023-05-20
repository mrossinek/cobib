"""coBib's Edit command.

This command can be used to manually edit database entries in their easily-readable YAML format.
To get started, simply type:
```
cobib edit <label>
```
which will open the YAML-formatted version of the specified `cobib.database.Entry` for editing.

You can configure which editor will be used via the `cobib.config.config.EditCommandConfig.editor`
setting which will default to using your `$EDITOR` environment setting (and fall back to `vim` if
that is not set).

You can even add entirely new entries to the database by specifying an unused entry label *and*
adding the `--add` command-line argument:
```
cobib edit --add <new label>
```
This entry will be entirely empty except for the one field which is always present:
    * `ENTRYTYPE`: set to the default value configured via
      `cobib.config.config.EditCommandConfig.default_entry_type`.

If you change the label of the entry during editing and you do *not* want your associated files to
automatically be renamed, you can provide the `--preserve-files` argument like so:
```
cobib edit --preserve-files <label>
```

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `e` key.
If you want to add a new entry manually, you will have to enter the prompt (defaults to `:`) and
then type out the command mentioned above:
```
:edit --add <new label>
```
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Type

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.parsers.yaml import YAMLParser
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class EditCommand(Command):
    """The Edit Command.

    This command can parse the following arguments:

        * `label`: the label of the entry to edit.
        * `-a`, `--add`: if specified, allows adding a new entry for a non-existent label. The
          default entry type of this new entry can be configured via
          `cobib.config.config.EditCommandConfig.default_entry_type`.
        * `--preserve-files`: skips the renaming of any associated files in case you manually rename
            the entry label during editing.
    """

    name = "edit"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: Type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.new_entry: Entry
        """A `cobib.database.Entry` instance edited by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="edit", description="Edit subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        parser.add_argument(
            "-a",
            "--add",
            action="store_true",
            help="if specified, will add a new entry for unknown labels",
        )
        parser.add_argument(
            "--preserve-files", action="store_true", help="do not rename associated files"
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Edit command.")

        Event.PreEditCommand.fire(self)

        yml = YAMLParser()

        bib = Database()

        try:
            entry = bib[self.largs.label]
            prv = yml.dump(entry)
            if self.largs.add:
                LOGGER.warning(
                    "Entry '%s' already exists! Ignoring the `--add` argument.", self.largs.label
                )
                self.largs.add = False
        except KeyError:
            # No entry for given label found
            if self.largs.add:
                # add a new entry for the unknown label
                entry = Entry(
                    self.largs.label,
                    {"ENTRYTYPE": config.commands.edit.default_entry_type},
                )
                prv = yml.dump(entry)
            else:
                msg = (
                    f"No entry with the label '{self.largs.label}' could be found."
                    "\nUse `--add` to add a new entry with this label."
                )
                LOGGER.error(msg)
                return
        if prv is None:
            # No entry found to be edited. This should never occur unless the YAMLParser experiences
            # an unexpected error.
            return

        LOGGER.debug("Creating temporary file.")
        with tempfile.NamedTemporaryFile(mode="w+", prefix="cobib-", suffix=".yaml") as tmp_file:
            tmp_file_name = tmp_file.name
            tmp_file.write(prv)
            tmp_file.flush()
            LOGGER.debug('Starting editor "%s".', config.commands.edit.editor)
            status = os.system(config.commands.edit.editor + " " + tmp_file.name)
            assert status == 0
            LOGGER.debug("Editor finished successfully.")
            new_entries = YAMLParser().parse(tmp_file.name)
            self.new_entry = list(new_entries.values())[0]
        assert not Path(tmp_file_name).exists()
        if entry == self.new_entry and not self.largs.add:
            LOGGER.info("No changes detected.")
            return

        bib.update({self.new_entry.label: self.new_entry})

        preserve_files = config.commands.edit.preserve_files or self.largs.preserve_files
        if preserve_files:
            LOGGER.info("Associated files will be preserved.")

        if self.new_entry.label != self.largs.label:
            bib.rename(self.largs.label, self.new_entry.label)
            if not preserve_files:
                new_files = []
                for file in self.new_entry.file:
                    path = RelPath(file)
                    if path.path.stem == self.largs.label:
                        LOGGER.info("Also renaming associated file '%s'.", str(path))
                        target = RelPath(path.path.parent / f"{self.new_entry.label}.pdf")
                        if target.path.exists():
                            LOGGER.warning("Found conflicting file, not renaming '%s'.", str(path))
                        else:
                            path.path.rename(target.path)
                            new_files.append(str(target))
                            continue
                    new_files.append(file)
                self.new_entry.file = new_files

        Event.PostEditCommand.fire(self)
        bib.save()

        self.git()

        msg = f"'{self.largs.label}' was successfully edited."
        LOGGER.info(msg)
