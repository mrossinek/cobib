"""coBib's Note command.

This command allows you to manipulate a note for an entry in your database. More precisely, it
allows you to show, edit, and delete the file linked to by the `cobib.database.entry.Entry.note`
field.

.. note::
   The *benefit* of the `cobib.database.entry.Entry.note` field over a file attached via the
   `cobib.database.entry.Entry.file` field is, that the note's contents are known to be plain-text
   and, thus, their content is included during the `cobib.commands.search.SearchCommand`.

The different actions that you can execute are very simple:

1. Show the note's contents:
   ```
   cobib note Label1 show
   ```

2. Edit the note's contents using `cobib.config.config.EditCommandConfig.editor`:
   ```
   cobib note Label1 edit
   ```

3. Delete the associated note:
   ```
   cobib note Label1 delete
   ```

When an entry does not have an associated note yet, the `edit` action will create a new empty note
for you. Its file location is determined as described in `NoteCommand.note_path`.

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `n` key which will load the note's content into the
`cobib.ui.components.note_view.NoteView` widget and start the editing process.
You can also preview the note's content using the `Enter` key.
The widget provides a few more features which it documents itself, so be sure to read that, too.
"""

from __future__ import annotations

import argparse
import logging
import os

from rich.console import ConsoleRenderable
from rich.syntax import Syntax
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.utils.context import get_active_app
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class NoteCommand(Command):
    """The Note Command.

    This command can parse the following arguments:

        * `label`: the label of the entry whose note to act upon.
        * `action`: the action to perform on the note. The following options are available:
            - `edit`: opens the note in an external editor.
            - `show`: prints the note contents.
            - `delete`: deletes the associated note.
    """

    name = "note"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.note_content: str | None = None
        """The text content of the note. This may be `None` for a non-existent note."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="note", description="Note subcommand parser.", exit_on_error=True
        )
        parser.add_argument("label", type=str, help="label of the entry")
        parser.add_argument(
            "action",
            help="the action to perform on the note",
            choices=("edit", "show", "delete", "_inline"),
            default="edit",
            nargs="?",
        )
        cls.argparser = parser

    @staticmethod
    def note_path(entry: Entry) -> RelPath:
        """Generates the default path of a note file.

        Given an `cobib.database.entry.Entry`, the default path is determined as follows:
          - the filename is simply the `cobib.database.entry.Entry.label`
          - the filetype is configured via `cobib.config.config.NoteCommandConfig.default_filetype`
          - the location is adjacent to `cobib.config.config.DatabaseConfig.file`

        Alternatively, if the `cobib.database.entry.Entry.note` attribute is already set, that path
        is used unmodified.

        Args:
            entry: the `cobib.database.entry.Entry` whose note path to generate.

        Returns:
            The `cobib.utils.rel_path.RelPath` to the note file.
        """
        path_str = entry.note
        if path_str is None:
            filename = f"{entry.label}.{config.commands.note.default_filetype}"
            path = RelPath(RelPath(config.database.file).path.with_name(filename))
        else:
            path = RelPath(path_str)

        return path

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Note command.")

        Event.PreNoteCommand.fire(self)

        bib = Database()

        try:
            entry = bib[self.largs.label]
        except KeyError:
            # No entry for given label found
            msg = f"No entry with the label '{self.largs.label}' could be found."
            LOGGER.error(msg)
            return

        # NOTE: We hack into the note field and provide an otherwise impossible value in order to
        # detect faulty data in this field from versions prior to the existence of the note command.
        if entry.note is False:  # type: ignore[comparison-overlap]
            LOGGER.error(  # type: ignore[unreachable]
                "The 'note' field of the '%s' entry is faulty! Check the logs during the loading of"
                " the database or the `lint` command for more details.",
                entry.label,
            )
            return

        path = self.note_path(entry)

        task_desc = ""

        if self.largs.action == "edit":
            self.edit(path)
            if not path.path.exists():
                msg = (
                    f"Could not find the note file associated with '{self.largs.label}'. Skipping "
                    "any further actions. Check the following path if you believe this to be an "
                    f"error: '{path}'"
                )
                LOGGER.warning(msg)
                return
            entry.note = str(path)
            bib.update({entry.label: entry})
            bib.save()
            task_desc = "edited"

        elif self.largs.action == "show":
            try:
                self.note_content = open(path.path, "r", encoding="utf-8").read()
            except FileNotFoundError as exc:
                LOGGER.error(
                    "Encountered the following error while trying to read the note of the entry "
                    f"'{self.largs.label}':"
                )
                LOGGER.error(exc)
            task_desc = "shown"

        elif self.largs.action == "delete":
            path.path.unlink(missing_ok=True)
            if path.path.exists():
                # NOTE: it should be impossible to get here unless the .unlink() call above fails
                # for some reason
                msg = (  # pragma: no cover
                    f"Could not delete the note file associated with '{self.largs.label}'. Check "
                    f"the following path: '{path}'"
                )
                LOGGER.warning(msg)  # pragma: no cover
                return  # pragma: no cover
            try:
                entry.note = None
            except KeyError:
                msg = f"The entry '{self.largs.label}' did not have an associated note!"
                LOGGER.warning(msg)
            bib.update({entry.label: entry})
            bib.save()
            task_desc = "deleted"

        elif self.largs.action == "_inline":
            LOGGER.info(
                "An inline note edit was performed. This command is merely executed to ensure it "
                "gets committed into any git history tracking."
            )
            entry.note = str(path)
            bib.update({entry.label: entry})
            bib.save()
            task_desc = "edited"

        else:
            LOGGER.warning(
                f"Encountered unexpected command action: '{self.largs.action}'! "
                "Don't know what to do!"
            )
            task_desc = "ignored"

        Event.PostNoteCommand.fire(self)

        self.git(add_files=[str(path)])

        msg = f"The note of '{self.largs.label}' was successfully {task_desc}."
        LOGGER.info(msg)

    @staticmethod
    def edit(path: RelPath) -> None:
        """Spawns an editor in the terminal to edit the provided file.

        Args:
            path: the file to edit.
        """
        app = get_active_app()
        if app is None:
            NoteCommand._edit(path)
        else:
            with app.suspend():  # pragma: no cover
                NoteCommand._edit(path)  # pragma: no cover

    @staticmethod
    def _edit(path: RelPath) -> None:
        LOGGER.debug('Starting editor "%s".', config.commands.edit.editor)
        status = os.system(config.commands.edit.editor + " " + str(path))
        if status == 0:
            LOGGER.debug("Editor finished successfully.")
        else:
            LOGGER.error(
                f'The note editing using "{config.commands.edit.editor}" failed with the following '
                f"error code: {status}"
            )

    @override
    def render_rich(self) -> ConsoleRenderable | None:
        if self.note_content is None:
            return None
        syntax = Syntax(
            self.note_content,
            config.commands.note.default_filetype,
            theme=config.theme.syntax.get_theme(),
            background_color=config.theme.syntax.get_background_color(),
            line_numbers=config.theme.syntax.line_numbers,
            word_wrap=True,
        )
        return syntax
