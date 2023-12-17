"""coBib's selection filter.

This is a simple [`LineFilter`](https://textual.textualize.io/api/filter/#textual.filter.LineFilter)
used to visually style the interactive selection.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from rich.segment import Segment
from rich.style import Style
from textual.color import Color
from textual.filter import LineFilter
from typing_extensions import override


class SelectionFilter(LineFilter):
    """coBib's selection filter."""

    def __init__(self) -> None:
        """Initializes the filter."""
        self.active: bool = False
        """Indicates whether the filter is active, i.e. the selection is not empty."""
        self.selection: set[str] = set()
        """The set of selected labels."""
        self.selection_style = Style(color="white", bgcolor="magenta")
        """The style applied to selected labels."""

    @override
    def apply(self, segments: list[Segment], background: Color | None = None) -> list[Segment]:
        return [
            Segment(
                text,
                self.selection_style
                if any(sel == text.strip() for sel in self.selection)
                else style,
                None,
            )
            for text, style, _ in segments
        ]
