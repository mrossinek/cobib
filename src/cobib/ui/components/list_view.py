"""coBib's list results viewer widget.

This widget gets produces by `cobib.commands.list.ListCommand.render_textual`.
It subclasses textual's built-in `DataTable` widget.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.geometry import Region, clamp
from textual.widgets import DataTable
from textual.widgets.data_table import RowDoesNotExist
from typing_extensions import override

from cobib.config import config

from .motion_key import MotionKey


class ListView(DataTable[Text]):
    """coBib's list results viewer widget."""

    id = "cobib-list-view"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
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
    | j, down | Moves one row down. |
    | k, up | Moves one row up. |
    | h, left | Moves to the left. |
    | l, right | Moves to the right. |
    | PageDown | Moves one page down. |
    | PageUp | Moves one page up. |
    | End | Moves to the bottom of the list. |
    | Home | Moves to the top of the list. |
    """

    DEFAULT_CSS = """
        ListView {
            height: 1fr;
        }
    """

    @property
    @override
    def scrollable_content_region(self) -> Region:
        # we shrink the scroll-able content region by the scroll offset at the bottom
        # NOTE: shrinking at the top does not seem to yield the intended result as it merely adds to
        # the offset at the bottom
        return super().scrollable_content_region.shrink((0, 0, config.tui.scroll_offset, 0))

    @override
    def validate_scroll_y(self, value: float) -> float:
        if not self.vertical_scrollbar.grabbed:
            # we implement the scroll offset at the top by forcing the scroll y value to be at
            # least an offset away from the cursor row
            if self.cursor_row - value < config.tui.scroll_offset:
                value = self.cursor_row - config.tui.scroll_offset
        return clamp(value, 0, self.row_count)

    @override
    def on_mount(self) -> None:
        self.fixed_columns = 1
        self.zebra_stripes = True
        self.cursor_type = "row"

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

    def get_current_label(self) -> str | None:
        """Gets the label of the entry currently under the cursor.

        Returns:
            The label of the entry currently under the cursor.
        """
        label = self.coordinate_to_cell_key(Coordinate(self.cursor_row, 0)).row_key.value
        return label

    def jump_to_label(self, label: str) -> None:
        """Jumps to the requested label.

        Args:
            label: the label to jump to.

        Raises:
            KeyError: when the label was not found in the current view.
        """
        try:
            idx = self.get_row_index(label)
        except RowDoesNotExist as exc:
            raise KeyError from exc
        self.move_cursor(row=idx, animate=True)
