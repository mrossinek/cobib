"""Delete entries.

.. include:: ../man/cobib-delete.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.prompt import Confirm
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class DeleteCommand(Command):
    """The Delete Command.

    This command can parse the following arguments:

        * `labels`: one (or multiple) labels of the entries to be deleted.
        * `-y`, `--yes`: skips the interactive confirmation prompt before performing the actual
          deletion. This overwrites the `cobib.config.config.DeleteCommand.confirm` setting.
        * `--preserve-files`: skips the deletion of any associated files. This overwrites the
          `cobib.config.config.DeleteCommandConfig.preserve_files` setting.
        * `--no-preserve-files`: does NOT skip the deletion of any associated files. This overwrites
          the `cobib.config.config.DeleteCommandConfig.preserve_files` setting.
    """

    name = "delete"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.deleted_entries: set[str] = set()
        """A set of labels which were deleted by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="delete",
            description="Delete subcommand parser.",
            epilog="Read cobib-delete.1 for more help.",
        )
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        parser.add_argument("-y", "--yes", action="store_true", help="confirm deletion")
        preserve_files_group = parser.add_mutually_exclusive_group()
        preserve_files_group.add_argument(
            "--preserve-files",
            action="store_true",
            default=None,
            help="do not delete associated files",
        )
        preserve_files_group.add_argument(
            "--no-preserve-files",
            dest="preserve_files",
            action="store_false",
            default=None,
            help="delete associated files",
        )
        cls.argparser = parser

    @override
    async def execute(self) -> None:  # type: ignore[override]
        LOGGER.debug("Starting Delete command.")

        Event.PreDeleteCommand.fire(self)

        preserve_files = config.commands.delete.preserve_files
        if self.largs.preserve_files is not None:
            preserve_files = self.largs.preserve_files
        LOGGER.info("Associated files will%s be preserved.", "" if preserve_files else " not")

        bib = Database()
        for label in self.largs.labels:
            try:
                LOGGER.debug("Attempting to delete entry '%s'.", label)

                if config.commands.delete.confirm and not self.largs.yes:
                    prompt_text = f"Are you sure you want to delete the entry '{label}'?"

                    res = await Confirm.ask(prompt_text, default=True)
                    if not res:
                        continue

                entry = bib.pop(label)
                if not preserve_files:
                    for file in entry.file:
                        path = RelPath(file)
                        LOGGER.debug("Attempting to remove associated file '%s'.", str(path))
                        path.path.unlink(missing_ok=True)

                self.deleted_entries.add(label)
            except KeyError:
                pass

        Event.PostDeleteCommand.fire(self)
        bib.save()

        self.git()

        for label in self.deleted_entries:
            msg = f"'{label}' was removed from the database."
            LOGGER.info(msg)
