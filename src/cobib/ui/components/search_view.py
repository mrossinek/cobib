"""coBib's search results viewer widget.

This widget gets produces by `cobib.commands.search.SearchCommand.render_textual`.
It subclasses textual's built-in `Tree` widget.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from rich.text import Text
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.widgets import Tree
from typing_extensions import override

from .motion_key import MotionKey


class SearchView(Tree[Text]):
    """coBib's search results viewer widget."""

    id = "cobib-search-view"

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

    @override
    def on_mount(self) -> None:
        self.show_root = False

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
        previous_node, current_node = self.cursor_node, self.cursor_node
        if current_node is None:
            raise NoMatches  # pylint: disable=raise-missing-from
        while current_node.parent is not None:
            previous_node, current_node = current_node, current_node.parent
        if previous_node is None:
            raise NoMatches  # pylint: disable=raise-missing-from
        label = str(previous_node.label).split(" - ", maxsplit=1)[0]
        return label
