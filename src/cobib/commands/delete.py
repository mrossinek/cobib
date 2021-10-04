"""coBib's Delete command.

This command can be used to deleted entries from the database.
```
cobib delete <label 1> [<label 2> ...]
```

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `d` key.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import IO, TYPE_CHECKING, Any, List

from cobib.config import Event
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class DeleteCommand(Command):
    """The Delete Command."""

    name = "delete"

    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Deletes an entry.

        This command deletes one (or multiple) entries from the database.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `labels`: one (or multiple) labels of the entries to be deleted.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Delete command.")
        parser = ArgumentParser(prog="delete", description="Delete subcommand parser.")
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        parser.add_argument(
            "--preserve-files", action="store_true", help="do not delete associated files"
        )

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return

        Event.PreDeleteCommand.fire(largs)

        deleted_entries = set()

        bib = Database()
        for label in largs.labels:
            try:
                LOGGER.debug("Attempting to delete entry '%s'.", label)
                entry = bib.pop(label)
                if not largs.preserve_files:
                    for file in entry.file:
                        path = RelPath(file)
                        try:
                            LOGGER.debug("Attempting to remove associated file '%s'.", str(path))
                            os.remove(path.path)
                        except FileNotFoundError:
                            pass

                deleted_entries.add(label)
            except KeyError:
                pass

        Event.PostDeleteCommand.fire(deleted_entries)
        bib.save()

        self.git(args=vars(largs))

        for label in deleted_entries:
            msg = f"'{label}' was removed from the database."
            LOGGER.info(msg)

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Delete command triggered from TUI.")
        if tui.selection:
            # use selection for command
            labels = list(tui.selection)
            tui.selection.clear()
        else:
            # get current label
            label, _ = tui.viewport.get_current_label()
            labels = [label]
        # delete selected entry
        tui.execute_command(["delete"] + labels, skip_prompt=True)
        # update database list
        LOGGER.debug("Updating list after Delete command.")
        tui.viewport.update_list()
