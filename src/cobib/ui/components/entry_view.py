"""coBib's entry viewer widget.

This widget gets used to display the result of `cobib.commands.show.ShowCommand.render_textual`.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from typing_extensions import override


class EntryView(VerticalScroll):
    """coBib's entry viewer widget."""

    DEFAULT_CSS = """
        EntryView {
            height: 1fr;
            width: 1fr;
        }
    """

    @override
    def compose(self) -> ComposeResult:
        yield Static()
