"""coBib's entry viewer widget.

This widget merely renders its reactive `EntryView.string` variable to the screen. It is intended to
display the result of `cobib.commands.show.ShowCommand.render_textual`.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from rich.console import RenderableType
from textual.reactive import reactive
from textual.widget import Widget
from typing_extensions import override


class EntryView(Widget, can_focus=False, can_focus_children=False):
    """coBib's entry viewer widget."""

    DEFAULT_CSS = """
        EntryView {
            width: 1fr;
        }
    """

    string: reactive[RenderableType] = reactive("")
    """The [reactive](https://textual.textualize.io/guide/reactivity/) string-representation of the
    current entry."""

    @override
    def render(self) -> RenderableType:
        return self.string
