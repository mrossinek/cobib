"""coBib's Delete command.

This command can be used to deleted entries from the database.
```
cobib delete <label 1> [<label 2> ...]
```

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `d` key.
"""

from __future__ import annotations

import logging
import os
from typing import List, Set

from cobib.config import Event
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class DeleteCommand(Command):
    """The Delete Command."""

    name = "delete"

    def __init__(self, args: List[str]) -> None:
        """TODO."""
        super().__init__(args)

        self.deleted_entries: Set[str] = set()

    @classmethod
    def init_argparser(cls) -> None:
        """TODO."""
        parser = ArgumentParser(prog="delete", description="Delete subcommand parser.")
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        parser.add_argument(
            "--preserve-files", action="store_true", help="do not delete associated files"
        )
        cls.argparser = parser

    def execute(self) -> None:
        """Deletes an entry.

        This command deletes one (or multiple) entries from the database.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `labels`: one (or multiple) labels of the entries to be deleted.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
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
