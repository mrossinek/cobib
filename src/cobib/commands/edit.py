"""Edit an entry.

.. include:: ../man/cobib-edit.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
from pathlib import Path

from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.parsers.yaml import YAMLParser
from cobib.utils.context import get_active_app
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class EditCommand(Command):
    """The Edit Command.

    This command can parse the following arguments:

        * `label`: the label of the entry to edit.
        * `-a`, `--add`: if specified, allows adding a new entry for a non-existent label. The
          default entry type of this new entry can be configured via
          `cobib.config.config.EditCommandConfig.default_entry_type`.
        * `--preserve-files`: skips the renaming of any associated files in case you manually rename
          the entry label during editing. This overwrites the
          `cobib.config.config.EditCommandConfig.preserve_files` setting.
        * `--no-preserve-files`: does NOT skip the renaming of any associated files in case you
          manually rename the entry label during editing. This overwrites the
          `cobib.config.config.EditCommandConfig.preserve_files` setting.
    """

    name = "edit"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.new_entry: Entry
        """A `cobib.database.Entry` instance edited by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="edit",
            description="Edit subcommand parser.",
            epilog="Read cobib-edit.1 for more help.",
        )
        parser.add_argument("label", type=str, help="label of the entry")
        parser.add_argument(
            "-a",
            "--add",
            action="store_true",
            help="if specified, will add a new entry for unknown labels",
        )
        preserve_files_group = parser.add_mutually_exclusive_group()
        preserve_files_group.add_argument(
            "--preserve-files",
            action="store_true",
            default=None,
            help="do NOT rename associated files",
        )
        preserve_files_group.add_argument(
            "--no-preserve-files",
            dest="preserve_files",
            action="store_false",
            default=None,
            help="rename associated files",
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
            entry_text = yml.dump(entry)
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
                entry_text = yml.dump(entry)
            else:
                msg = (
                    f"No entry with the label '{self.largs.label}' could be found."
                    "\nUse `--add` to add a new entry with this label."
                )
                LOGGER.error(msg)
                return
        if entry_text is None:
            # No entry found to be edited. This should never occur unless the YAMLParser experiences
            # an unexpected error.
            LOGGER.error(  # pragma: no cover
                f"Encountered an unexpected case while trying to edit {self.largs.label} which "
                "might result from a problem with the YAML parser."
            )
            return  # pragma: no cover

        new_text = self.edit(entry_text)

        if entry_text == new_text and not self.largs.add:
            LOGGER.info("No changes detected.")
            return

        parsed = yml.parse(new_text)
        self.new_entry = next(iter(parsed.values()))

        bib.update({self.new_entry.label: self.new_entry})

        preserve_files = config.commands.edit.preserve_files
        if self.largs.preserve_files is not None:
            preserve_files = self.largs.preserve_files
        LOGGER.info("Associated files will%s be preserved.", "" if preserve_files else " not")

        if self.new_entry.label != self.largs.label:
            bib.rename(self.largs.label, self.new_entry.label)
            if not preserve_files:
                new_files = []
                for file in self.new_entry.file:
                    path = RelPath(file)
                    if path.path.stem == self.largs.label:
                        LOGGER.info("Also renaming associated file '%s'.", str(path))
                        target = RelPath(path.path.with_stem(self.new_entry.label))
                        if target.path.exists():
                            LOGGER.warning(  # pragma: no cover
                                "Found conflicting file, not renaming '%s'.", str(path)
                            )
                        else:
                            path.path.rename(target.path)
                            new_files.append(str(target))
                            continue
                    new_files.append(file)  # pragma: no cover
                self.new_entry.file = new_files

        Event.PostEditCommand.fire(self)
        bib.save()

        self.git()

        msg = f"'{self.largs.label}' was successfully edited."
        LOGGER.info(msg)

    @staticmethod
    def edit(entry_text: str) -> str:
        """Spawns an editor in the terminal to edit the provided entry text.

        Args:
            entry_text: the entry in text form to edit.

        Returns:
            The new entry.
        """
        app = get_active_app()
        if app is None:
            return EditCommand._edit(entry_text)
        # NOTE: we are unable to test this in CI at this time, because the textual Pilot interface
        # does not support suspend.
        with app.suspend():
            return EditCommand._edit(entry_text)

    @staticmethod
    def _edit(entry_text: str) -> str:
        LOGGER.debug("Creating temporary file.")
        with tempfile.NamedTemporaryFile(mode="w+", prefix="cobib-", suffix=".yaml") as tmp_file:
            tmp_file_name = tmp_file.name
            tmp_file.write(entry_text)
            tmp_file.flush()
            LOGGER.debug('Starting editor "%s".', config.commands.edit.editor)
            status = os.system(config.commands.edit.editor + " " + tmp_file.name)
            assert status == 0
            LOGGER.debug("Editor finished successfully.")
            new_text = open(tmp_file.name, "r", encoding="utf-8").read()
        assert not Path(tmp_file_name).exists()
        return new_text
