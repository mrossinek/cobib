"""coBib's `logging.Handler` for interactive UIs.

This handler is used by the `cobib.ui.tui.TUI` to render logging messages as
`cobib.ui.components.popup.Popup` instances.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typing_extensions import override

from .popup import Popup

if TYPE_CHECKING:
    from ..tui import TUI


class PopupLoggingHandler(logging.Handler):
    """coBib's `logging.Handler` for interactive UIs."""

    def __init__(self, app: TUI, level: int = logging.INFO) -> None:
        """Initializes the handler.

        Args:
            app: the running TUI instance.
            level: the default logging level to be displayed.
        """
        super().__init__(level=level)

        self._app = app

        formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
        self.setFormatter(formatter)

        for handler in self._app.root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                self._app.root_logger.removeHandler(handler)
                handler.close()

        self._app.root_logger.addHandler(self)

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self._app.print(Popup(self.format(record), level=record.levelno))
