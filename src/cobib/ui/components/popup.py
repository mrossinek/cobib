"""coBib's popup widget.

This widget renders as a simple popup. For example, it is used to display logging information.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import logging
from typing import Any

from rich.console import RenderableType
from textual.widgets import Label


class Popup(Label, can_focus=False, can_focus_children=False):
    """coBib's popup widget."""

    DEFAULT_CSS = """
        Popup {
            text-style: bold;
            min-height: 1;
            width: 100%;
            color: auto;
        }
    """

    def __init__(
        self,
        renderable: RenderableType,
        *args: Any,
        level: int = logging.INFO,
        timer: float | None = 5.0,
        **kwargs: Any,
    ) -> None:
        """Initializes the popup.

        Args:
            renderable: the contents of the popup.
            *args: any further positional arguments for the underlying `Label` class.
            level: the `logging` level which this popup references. The popup's back- and foreground
                colors are styled according to this setting. Setting this to `0` will use the
                default styling.
            timer: an optional number of seconds after which to automatically remove the popup.
            **kwargs: any further keyword arguments for the underlying `Label` class.
        """
        super().__init__(renderable, *args, **kwargs)
        if level >= logging.CRITICAL:
            self.styles.background = "red"
            self.styles.color = "yellow"
        elif level >= logging.ERROR:
            self.styles.background = "red"
        elif level >= logging.WARNING:
            self.styles.background = "yellow"
        elif level >= logging.INFO:
            self.styles.background = "green"
        elif level >= logging.DEBUG:
            self.styles.background = "blue"
        if timer is not None:
            self.set_timer(timer, self.remove)
