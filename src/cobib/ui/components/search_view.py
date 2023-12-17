"""coBib's search results viewer widget.

This widget gets produces by `cobib.commands.search.SearchCommand.render_textual`.
It subclasses textual's built-in `Tree` widget.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import ClassVar, Union

from rich.text import Text
from textual.binding import Binding
from textual.widgets import Tree
from typing_extensions import override

from .motion_key import MotionKey


class SearchView(Tree[Union[str, Text]]):
    """coBib's search results viewer widget."""

    id = "cobib-search-view"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("enter", "toggle_all", "Toggle All"),
        Binding("j", "motion('down', 'cursor_down')", "Down", show=False),
        Binding("k", "motion('up', 'cursor_up')", "Up", show=False),
        Binding("h", "motion('left', 'cursor_left')", "Left", show=False),
        Binding("l", "motion('right', 'cursor_right')", "Right", show=False),
        Binding("down", "motion('down', 'cursor_down')", "Down", show=False),
        Binding("up", "motion('up', 'cursor_up')", "Up", show=False),
        Binding("left", "motion('left', 'cursor_left')", "Left", show=False),
        Binding("right", "motion('right', 'cursor_right')", "Right", show=False),
        Binding("home", "motion('home', 'scroll_home')", "Home", show=False),
        Binding("end", "motion('end', 'scroll_end')", "End", show=False),
        Binding("pageup", "motion('pageup', 'page_up')", "Page Up", show=False),
        Binding("pagedown", "motion('pagedown', 'page_down')", "Page Down", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | space | Toggle the expand/collapsed space of the current item. |
    | enter | Toggle the expand/collapsed space of the current item and all its children. |
    | j, down | Moves one row down. |
    | k, up | Moves one row up. |
    | h, left | Moves to the left. |
    | l, right | Moves to the right. |
    | PageDown | Moves one page down. |
    | PageUp | Moves one page up. |
    | End | Moves to the bottom of the tree. |
    | Home | Moves to the top of the tree. |
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

    def action_toggle_all(self) -> None:
        """Toggles the expansion of the current node and all of its children recursively."""
        if self.cursor_node is not None:
            self.cursor_node.toggle_all()

    def get_current_label(self) -> str | None:
        """Gets the label of the entry currently under the cursor.

        Returns:
            The label of the entry currently under the cursor.
        """
        if self.cursor_node is None:
            return None
        return str(self.cursor_node.data)

    def jump_to_label(self, label: str) -> None:
        """Jumps to the requested label.

        Args:
            label: the label to jump to.

        Raises:
            KeyError: when the label was not found in the current view.
        """
        for child in self.root.children:
            if child.data == label:
                self.select_node(child)
                self.scroll_to_node(child, animate=True)
                break
        else:
            raise KeyError
