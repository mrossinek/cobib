"""coBib's `logging.Handler` for interactive UIs.

This handler is used by the `cobib.ui.tui.TUI` to render logging messages inside of the
`cobib.ui.components.log_screen.LogScreen`.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from rich.text import Text
from typing_extensions import override

from cobib.utils.logging import DEPRECATED, HINT

if TYPE_CHECKING:
    from ..ui import UI


class LoggingHandler(logging.Handler, ABC):
    """coBib's `logging.Handler` for interactive UIs."""

    FORMAT: str = "%(asctime)s [%(levelname)s] %(message)s"
    """The Formatter `fmt` string."""

    DATE_FORMAT: str = "%H:%M:%S"
    """The Formatter `datefmt` string."""

    def __init__(self, ui: UI, level: int = logging.INFO) -> None:
        """Initializes the handler.

        Args:
            ui: the running UI instance.
            level: the default logging level to be displayed.
        """
        super().__init__(level=level)

        self.ui = ui

        formatter = logging.Formatter(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)
        self.setFormatter(formatter)

        for handler in self.ui.root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) or (
                # NOTE: the second condition is required to ensure the unittests pass in Python 3.9
                isinstance(handler, LoggingHandler) and not isinstance(handler, self.__class__)
            ):
                self.ui.root_logger.removeHandler(handler)
                handler.close()

        self.ui.root_logger.addHandler(self)

    @override
    def format(self, record: logging.LogRecord) -> Text:  # type: ignore[override]
        message = super().format(record)

        style = ""
        if record.levelno >= logging.CRITICAL:
            style = "bold red"
        elif record.levelno >= DEPRECATED:
            style = "bold yellow"
        elif record.levelno >= logging.ERROR:
            style = "red"
        elif record.levelno >= HINT:
            style = "bold green"
        elif record.levelno >= logging.WARNING:
            style = "yellow"
        elif record.levelno >= logging.INFO:
            style = "green"
        elif record.levelno >= logging.DEBUG:  # pragma: no branch
            style = "blue"

        message = message.replace(
            f"[{record.levelname}]", f"[{style}][{record.levelname}][/{style}]"
        )

        text = Text.from_markup(message)
        return text

    @abstractmethod
    @override
    def emit(self, record: logging.LogRecord) -> None: ...
