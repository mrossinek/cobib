"""coBib's popup panel widget.

This widget is merely a container for placing all the `cobib.ui.components.popup.Popup` instances.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from textual.containers import Container


class PopupPanel(Container, can_focus=False, can_focus_children=False):
    """coBib's popup panel widget."""

    DEFAULT_CSS = """
        PopupPanel {
            layer: popup;
            layout: vertical;
            align: center bottom;
            width: 100%;
            height: auto;
            offset-y: -1;
        }
    """
