"""coBib's main viewport widget.

This widget is currently the main viewport of the `cobib.ui.tui.TUI`.

.. warning::

   The TUI is pending a refactoring to make use of textual's
   [Screens](https://textual.textualize.io/guide/screens/) in order to handle different contexts
   such as displaying the results of `cobib.commands.list.ListCommand.render_textual` and
   `cobib.commands.search.SearchCommand.render_textual`. This will remove the need for this widget.

   For more information refer to [this issue](https://gitlab.com/cobib/cobib/-/issues/111).

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from textual.containers import Container


# TODO: refactor TUI to make use of Screens instead.
class MainView(Container):
    """coBib's main viewport widget."""

    DEFAULT_CSS = """
        MainView {
            width: 2fr;
        }
    """

    def clear(self) -> None:
        """Clears this widget.

        By design, this widget always has a single child mounted to it, which this method removes.
        """
        self.query("Widget").remove()
