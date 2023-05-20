"""coBib's help popup.

This widget renders a popup with the current key bindings and action descriptions.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import cast

from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static
from typing_extensions import override


class HelpPopup(Container, can_focus=False, can_focus_children=False):
    """coBib's help popup."""

    DEFAULT_CSS = """
        HelpPopup {
            layer: overlay;
            background: blue 25%;
            height: auto;
            width: 100%;
        }

        HelpPopup.-hidden {
            offset-y: 100%;
        }
    """

    HELP_DESCRIPTIONS = [
        ("q", "Quit's coBib"),
        ("question_mark", "Toggles the help page"),
        ("underscore", "Toggles between the horizontal and vertical layout"),
        ("space", "Toggles folding of a search result"),
        ("colon", "Starts the prompt for an arbitrary coBib command"),
        ("v", "Selects the current entry"),
        ("slash", "Searches the database for the provided string"),
        ("a", "Prompts for a new entry to be added to the database"),
        ("d", "Delete the current (or selected) entries"),
        ("e", "Edits the current entry"),
        ("f", "Allows filtering the table using `++/--` keywords"),
        ("i", "Imports entries from another source"),
        ("m", "Prompts for a modification (respects selection)"),
        ("o", "Opens the current (or selected) entries"),
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
        help_table = Table(title="coBib TUI Help")
        help_table.add_column("Key")
        help_table.add_column("Description")
        if self.parent is None:
            raise KeyError
        app = cast(App[None], self.parent.parent)
        for key, description in self.HELP_DESCRIPTIONS:
            help_table.add_row(app.get_key_display(key), description)
        static = Static(help_table)
        static.styles.content_align = ("center", "middle")
        yield static
