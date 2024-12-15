"""coBib's note viewer widget.

This widget gets used to display and edit the contents of the note associated with the currently
selected entry.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from textual.binding import Binding
from textual.reactive import Reactive
from textual.widgets import TextArea
from textual.widgets.text_area import Edit, EditResult
from typing_extensions import override

from cobib.config import config
from cobib.database import Database

from .main_content import MainContent

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class NoteView(TextArea):
    """coBib's note viewer widget."""

    DEFAULT_CSS = """
        NoteView {
            height: 1fr;
            width: 1fr;
            grid-size: 1 2;
            border: tall $accent;
        }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "escape", "Escape"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+x", "external", "External edit"),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | Escape | Unfocuses the text area. |
    | Ctrl+r | Reset any unsaved changes. |
    | Ctrl+s | Saves the text area contents. |
    | Ctrl+x | Opens the text area content in an external editor. |
    """

    PLACEHOLDER = (
        "Here you can view and edit the `note` associated with the current entry.\n"
        "Quickstart:\n"
        "  - hit `Enter` to load the associated note\n"
        "  - hit `n` to focus the text area and start editing\n"
        "  - hit `Escape` to unfocus the text area\n"
        "  - hit `Ctrl+s` to save the note\n"
        "  - hit `Ctrl+r` to discard any unsaved changes\n"
        "  - hit `Ctrl+x` to open the note for editing in an external editor\n"
    )

    unsaved: Reactive[bool] = Reactive(False, compute=False)
    """A reactive boolean indicating whether the view contains unsaved changes."""

    @override
    def on_mount(self) -> None:
        self.text = NoteView.PLACEHOLDER
        self.border_title = "Note"
        self.read_only = True

    @override
    def load_text(self, text: str) -> None:
        super().load_text(text)
        self.unsaved = False

    @override
    def edit(self, edit: Edit) -> EditResult:
        result = super().edit(edit)
        self.unsaved = True
        return result

    def watch_has_focus(self, value: bool) -> None:
        """Watches whether this widget has focus.

        Args:
            value: the new focus value.
        """
        super().watch_has_focus(value)
        self._update_border(value)
        if not value:
            self.read_only = True

    def watch_unsaved(self, value: bool) -> None:
        """Watches the state of `unsaved`.

        Args:
            value: the new value assigned to `unsaved`.
        """
        self.border_subtitle = "UNSAVED" if value else ""
        self._update_border(True)

    def _update_border(self, has_focus: bool) -> None:
        """Updates the border style depending on the state of the widget.

        Args:
            has_focus: whether the widget currently has focus (see also `watch_has_focus`).
        """
        if has_focus:
            if self.unsaved:
                self.styles.border = ("tall", config.theme.css_variables["warning"])
            else:
                self.styles.border = ("tall", config.theme.css_variables["success"])
        else:  # noqa: PLR5501
            if self.unsaved:
                self.styles.border = ("tall", config.theme.css_variables["error"])
            else:
                self.styles.border = ("tall", config.theme.css_variables["accent"])

    def action_escape(self) -> None:
        """The `Esc` key action to unfocus this widget."""
        main = self.app.query_one(MainContent)
        main_content = None if main.current is None else main.get_child_by_id(main.current)
        self.screen.set_focus(main_content)

    def action_reset(self) -> None:
        """The `Ctrl+r` key action to reset any unsaved changes."""
        label = self.border_title
        if not isinstance(label, str):
            raise RuntimeError("Expecting to extract a label from the border title!")

        LOGGER.info(f"Discarding any unsaved changes to the note of entry '{label}'.")
        self.load_note(label, escape=True, force_reload=True)

    def action_save(self) -> None:
        """The `Ctrl+s` key action to save the current changes."""
        self._save_contents("_inline")

    def action_external(self) -> None:
        """The `Ctrl+x` key action to open the note in an external editor."""
        self._save_contents("edit")

    def load_note(
        self,
        label: str,
        *,
        edit: bool = False,
        escape: bool = False,
        force_reload: bool = False,
    ) -> None:
        """Loads a note into this widget.

        Args:
            label: the label of the `cobib.database.entry.Entry` whose note to load.
            edit: whether to immediately focus this widget and start editing the contents (`True`)
                or leave the widget in read-only mode (`False`, default).
            escape: whether to trigger `action_escape` after loading the note.
            force_reload: whether to discard any unsaved changes.
        """
        if self.border_title != label or force_reload:
            if self.unsaved and not force_reload:
                msg = (
                    "You have unsaved changes on your open note! You must save or reset them before"
                    " being able to load a different note!\n"
                    "To do so, focus the note area (by clicking or navigating to the corresponding "
                    "entry and hitting 'n') and hit 'Ctrl+s' to save or 'Ctrl+r' to reset the note."
                )
                self.notify(msg, title="Error", severity="error", timeout=5)
                return

            self.border_title = label
            self.border_subtitle = None

            from cobib.commands import NoteCommand

            note_file = NoteCommand.note_path(Database()[label])

            if note_file.path.exists():
                self.text = open(note_file.path, "r", encoding="utf-8").read()
            else:
                self.text = ""

        self.unsaved = False

        if escape:
            self.action_escape()

        elif edit:
            self.read_only = False
            self.focus()

    def _save_contents(self, action: str) -> None:
        """Saves the contents of the widget into the note file on disk.

        Args:
            action: the `action` argument to the `cobib.commands.note.NoteCommand`.
        """
        label = self.border_title
        if not isinstance(label, str):
            raise RuntimeError("Expecting to extract a label from the border title!")

        from cobib.commands import NoteCommand

        note_file = NoteCommand.note_path(Database()[label])

        with open(note_file.path, "w", encoding="utf-8") as file:
            file.write(self.text)

        NoteCommand(label, action).execute()

        self.load_note(label, escape=True, force_reload=True)
