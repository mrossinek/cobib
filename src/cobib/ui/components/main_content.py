"""coBib's main content view.

This is a simple subclass of textual's `ContentSwitcher` widget. Any widget mounted into it is
expected to have a `get_current_label` method implement (although this is currently not
programmatically enforced). For examples refer to `cobib.ui.components.list_view.ListView` and
`cobib.ui.components.search_view.SearchView`.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import ContentSwitcher
from typing_extensions import override


class MainContent(ContentSwitcher):
    """coBib's main content view."""

    DEFAULT_CSS = """
        MainContent {
            width: 2fr;
        }
    """

    # TODO: add a validation hook to the mount method to prevent widgets of "wrong" type?

    def get_current_label(self) -> str:
        """Gets the label of the entry currently under the cursor.

        Raises:
            NoMatches: when `current` is `None`.

        Returns:
            The label of the entry currently under the cursor.
        """
        if self.current is None:
            raise NoMatches
        current_child = self.get_child_by_id(self.current)
        return current_child.get_current_label()  # type: ignore[no-any-return,attr-defined]

    async def replace_widget(self, widget: Widget) -> None:
        """Mounts the provided widget in-place of the one with the same `id`.

        Args:
            widget: the widget to be mounted.
        """
        if widget.id is None:
            return
        old_child = self.get_child_by_id(widget.id)
        await old_child.remove()
        self.mount(widget)
        self.current = widget.id
        self.refresh(layout=True)

    @override
    def notify_style_update(self) -> None:
        super().notify_style_update()
        if self.current is not None:
            current_child = self.get_child_by_id(self.current)
            current_child.notify_style_update()
            current_child.refresh()
