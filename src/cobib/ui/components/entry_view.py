"""coBib's entry viewer widget.

This widget gets used to display the result of `cobib.commands.show.ShowCommand.render_textual`.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.widgets import Static
from typing_extensions import override

from .note_view import NoteView


class EntryView(Grid):
    """coBib's entry viewer widget."""

    DEFAULT_CSS = """
        EntryView {
            height: 1fr;
            width: 1fr;
            grid-size: 1 2;
        }
    """

    @override
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static()
        yield NoteView()
