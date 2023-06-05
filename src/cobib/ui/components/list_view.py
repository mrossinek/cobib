"""coBib's list results viewer widget.

This widget gets produces by `cobib.commands.list.ListCommand.render_textual`.
It subclasses textual's built-in `DataTable` widget.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.reactive import reactive
from textual.widgets import DataTable
from typing_extensions import override

from .motion_key import MotionKey


class ListView(DataTable[Text]):
    """coBib's list results viewer widget."""

    id = "cobib-list-view"

    cursor_type = reactive("row")

    BINDINGS = [
        Binding("j", "motion('down', 'cursor_down')", "Down", show=False),
        Binding("k", "motion('up', 'cursor_up')", "Up", show=False),
        Binding("h", "motion('left', 'cursor_left')", "Left", show=False),
        Binding("l", "motion('right', 'cursor_right')", "Right", show=False),
        Binding("down", "motion('down', 'cursor_down')", "Down", show=False),
        Binding("up", "motion('up', 'cursor_up')", "Up", show=False),
        Binding("left", "motion('left', 'cursor_left')", "Left", show=False),
        Binding("right", "motion('right', 'cursor_right')", "Right", show=False),
        # TODO: add motions for home, end, page up, and page down
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | space | Toggle the expand/collapsed space of the current item. |
    | j, down | Moves one row down. |
    | k, up | Moves one row up. |
    | h, left | Moves to the left. |
    | l, right | Moves to the right. |
    """

    DEFAULT_CSS = """
        ListView {
            height: 1fr;
        }
    """

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # TODO: revisit this based on the outcome of https://github.com/Textualize/textual/pull/2740
        self.fixed_columns = 1
        self.zebra_stripes = True

    def action_motion(self, key: str, action: str) -> None:
        """Action to move the cursor.

        Under the hood, this delegates to the respective built-in cursor motion methods.
        However, this method also posts a `cobib.ui.components.motion_key.MotionKey` event.

        Args:
            key: the key which was pressed.
            action: the built-in action to trigger.
        """
        func = getattr(self, f"action_{action}", None)
        if func is not None:
            func()
        self.post_message(MotionKey(key))

    def get_current_label(self) -> str:
        """Gets the label of the entry currently under the cursor.

        Returns:
            The label of the entry currently under the cursor.
        """
        label = self.get_cell_at(Coordinate(self.cursor_row, 0)).plain
        return label
