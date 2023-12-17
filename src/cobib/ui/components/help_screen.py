"""coBib's help screen.

This screen renders a help information with the current key bindings and action descriptions.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import ClassVar

from rich.table import Table
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static
from typing_extensions import override


class HelpScreen(ModalScreen[None]):
    """coBib's help screen."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("question_mark", "toggle_help", "Help"),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | ? | Toggles the help screen. |
    """

    DEFAULT_CSS = """
        HelpScreen {
            align: center middle;
        }

        #help {
            padding: 1 2;
            width: auto;
            height: auto;
            background: $surface;
        }
    """

    HELP_DESCRIPTIONS: ClassVar[list[tuple[str, str]]] = [
        ("q", "Quit's coBib"),
        ("question_mark", "Toggles the help screen"),
        ("underscore", "Toggles between the horizontal and vertical layout"),
        ("space", "Toggles folding of a search result"),
        ("colon", "Starts the prompt for an arbitrary coBib command"),
        ("v", "Selects the current entry"),
        ("slash", "Searches the database for the provided string"),
        ("digit", "Immediately selects the preset filter given by that digit (0 = reset)"),
        ("a", "Prompts for a new entry to be added to the database"),
        ("d", "Deletes the current (or selected) entries"),
        ("e", "Edits the current entry"),
        ("f", "Allows filtering the table using `++/--` keywords"),
        ("i", "Imports entries from another source"),
        ("m", "Prompts for a modification (respects selection)"),
        ("o", "Opens the current (or selected) entries"),
        ("p", "Allows selecting a preset filter (see `config.tui.preset_filters`)"),
        ("r", "Redoes the last undone change. Requires git-tracking!"),
        ("s", "Prompts for the field to sort by (use -r to list in reverse)"),
        ("u", "Undes the last change. Requires git-tracking!"),
        ("x", "Exports the current (or selected) entries"),
        ("j", "Moves one row down"),
        ("k", "Moves one row up"),
        ("h", "Moves to the left"),
        ("l", "Moves to the right"),
    ]
    """The key binding help descriptions."""

    @override
    def compose(self) -> ComposeResult:
        help_table = Table(title="coBib TUI Help", caption="Close this help by pressing '?'")
        help_table.add_column("Key")
        help_table.add_column("Description")
        for key, description in self.HELP_DESCRIPTIONS:
            help_table.add_row(self.app.get_key_display(key), description)
        static = Static(help_table, id="help")
        static.styles.content_align = ("center", "middle")
        yield static

    def action_toggle_help(self) -> None:
        """Toggles the help information.

        Since this is the action of the `HelpScreen`, it simply pops the screen.
        """
        self.app.pop_screen()
