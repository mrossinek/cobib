"""coBib's `logging.Handler` for interactive UIs.

This handler is used by the `cobib.ui.tui.TUI` to render logging messages inside of the
`cobib.ui.components.log_screen.LogScreen`.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from rich.text import Text
from typing_extensions import override

from .log_screen import LogScreen

if TYPE_CHECKING:
    from ..tui import TUI


class LoggingHandler(logging.Handler):
    """coBib's `logging.Handler` for interactive UIs."""

    def __init__(self, app: TUI, level: int = logging.INFO) -> None:
        """Initializes the handler.

        Args:
            app: the running TUI instance.
            level: the default logging level to be displayed.
        """
        super().__init__(level=level)

        self._app = app

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        self.setFormatter(formatter)

        for handler in self._app.root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                self._app.root_logger.removeHandler(handler)
                handler.close()

        self._app.root_logger.addHandler(self)

    @override
    def format(self, record: logging.LogRecord) -> Text:  # type: ignore[override]
        message = super().format(record)

        style = ""
        if record.levelno >= logging.CRITICAL:
            style = "bold red"
        elif record.levelno >= logging.ERROR:
            style = "red"
        elif record.levelno >= logging.WARNING:
            style = "yellow"
        elif record.levelno >= logging.INFO:
            style = "green"
        elif record.levelno >= logging.DEBUG:
            style = "blue"

        text = Text(message, style)
        return text

    @override
    def emit(self, record: logging.LogRecord) -> None:
        log_screen = cast(LogScreen, self._app.get_screen("log"))
        log_screen.rich_log.write(self.format(record))
        if record.levelno >= logging.ERROR and not log_screen.is_current:
            self._app.push_screen("log")
