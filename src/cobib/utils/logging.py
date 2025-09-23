"""coBib's logging module.

This module provides utility methods to set up logging to different handlers as well as a custom
logging handler for prettified log formatting.
"""

from __future__ import annotations

import logging
import logging.handlers
from importlib import metadata
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import ConsoleRenderable, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from typing_extensions import override

from .console import PromptConsole
from .rel_path import RelPath

if TYPE_CHECKING:
    from cobib.ui.ui import UI

HINT = 35
"""The logging level value for HINT messages."""

DEPRECATED = 45
"""The logging level value for DEPRECATION messages."""

# NOTE: we add a custom HINT level which has a higher priority than WARNING and, thus, can be used
# to provide information to the user that might be useful to see at runtime.
logging.addLevelName(HINT, "HINT")
# NOTE: we also add a custom level DEPRECATED which has an even higher priority.
logging.addLevelName(DEPRECATED, "DEPRECATED")


class LoggingHandler(logging.Handler):
    """coBib's `logging.Handler`."""

    FORMAT: str = "[%(levelname)s] %(message)s"
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
            if isinstance(handler, (logging.StreamHandler, LoggingHandler)):
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

    @override
    def emit(self, record: logging.LogRecord) -> None:
        PromptConsole.get_instance().log(self.format(record))


def get_stream_handler(
    level: int = logging.WARNING,
) -> logging.StreamHandler:  # type: ignore[type-arg]
    """Returns a basic StreamHandler logging to a `StringIO` stream.

    Args:
        level: the logging level of this handler.
    """
    formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")

    handler = logging.StreamHandler(stream=StringIO())
    handler.setLevel(level)
    handler.setFormatter(formatter)

    return handler


def get_file_handler(
    level: str | int = "INFO", logfile: str | Path | None = None
) -> logging.handlers.RotatingFileHandler:
    """Returns a `RotatingFileHandler`.

    Args:
        level: the handler's logging level.
        logfile: the output path for the log file.
    """
    if logfile is None:
        from cobib.config import config  # noqa: PLC0415

        logfile = config.logging.logfile

    path = RelPath(logfile).path
    path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s %(funcName)s:%(lineno)d %(message)s"
    )

    handler = logging.handlers.RotatingFileHandler(
        filename=path,
        maxBytes=10485760,  # 10 Megabytes
        backupCount=10,
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)

    return handler


def print_changelog(version: str, cached_version_path: str | None) -> Panel | None:
    """Generates a `rich.Panel` to display the changelog since the last displayed version.

    This function prints the contents of the CHANGELOG (extracted from the package metadata)
    between the current version (`version`) and the latest cached version (extracted from the
    provided file path).

    Args:
        version: the currently running version of coBib.
        cached_version_path: the path to the file which caches the previously executed version of
            coBib. If `None`, this method exits early (thereby silencing this feature).

    Returns:
        An optional `rich.Panel` with the rendered Markdown.
    """
    if cached_version_path is None:
        return None

    _cached_version_path = RelPath(cached_version_path).path
    if not _cached_version_path.parent.exists():
        _cached_version_path.parent.mkdir(parents=True)

    try:
        current_version = version[: version.index("+")]
    except ValueError:
        current_version = version

    cached_version = None
    try:
        with open(_cached_version_path, "r", encoding="utf-8") as version_file:
            cached_version = version_file.read().strip()
    except FileNotFoundError:
        pass

    if current_version == cached_version:
        return None

    with open(_cached_version_path, "w", encoding="utf-8") as version_file:
        version_file.write(current_version)

    groups: list[ConsoleRenderable] = []
    groups.append(
        Text(
            "Hi there! It looks like you have updated coBib; here is what's new:",
            style="bold yellow",
        )
    )

    description = str(metadata.metadata("cobib").get("description"))

    lines: list[str] = []
    started = False
    for line in description.splitlines():
        line = line.rstrip()  # noqa: PLW2901
        if line.startswith(f"## [{current_version}]"):
            started = True
        elif line.startswith(f"## [{cached_version}]"):
            break

        if started:
            lines.append(line)

    groups.append(Markdown("\n".join(lines)))

    return Panel(Group(*groups))
