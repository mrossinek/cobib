"""coBib's Delete command.

This command can be used to deleted entries from the database.
```
cobib delete <label 1> [<label 2> ...]
```

If you want to preserve the files associated with the deleted entries, you can provide the
`--preserve-files` argument like so:
```
cobib delete --preserve-files <label 1> [<label 2> ...]
```

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `d` key.
"""

from __future__ import annotations

import logging
import os
from typing import Set, Type

from rich.console import Console
from rich.prompt import PromptBase
from textual.app import App
from typing_extensions import override

from cobib.config import Event
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class DeleteCommand(Command):
    """The Delete Command.

    This command can parse the following arguments:

        * `labels`: one (or multiple) labels of the entries to be deleted.
        * `--preserve-files`: skips the deletion of any associated files.
    """

    name = "delete"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: Type[PromptBase[str]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.deleted_entries: Set[str] = set()
        """A set of labels which were deleted by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="delete", description="Delete subcommand parser.")
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        parser.add_argument(
            "--preserve-files", action="store_true", help="do not delete associated files"
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Delete command.")

        Event.PreDeleteCommand.fire(self)

        bib = Database()
        for label in self.largs.labels:
            try:
                LOGGER.debug("Attempting to delete entry '%s'.", label)
                entry = bib.pop(label)
                if not self.largs.preserve_files:
                    for file in entry.file:
                        path = RelPath(file)
                        try:
                            LOGGER.debug("Attempting to remove associated file '%s'.", str(path))
                            os.remove(path.path)
                        except FileNotFoundError:
                            pass

                self.deleted_entries.add(label)
            except KeyError:
                pass

        Event.PostDeleteCommand.fire(self)
        bib.save()

        self.git()

        for label in self.deleted_entries:
            msg = f"'{label}' was removed from the database."
            LOGGER.info(msg)
