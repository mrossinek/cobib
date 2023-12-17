"""coBib's logging module.

This module provides utility methods to set up logging to different handlers.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from importlib import metadata
from pathlib import Path

from rich.console import ConsoleRenderable, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from typing_extensions import override

from .rel_path import RelPath

# NOTE: we add a custom HINT level which has a higher priority than WARNING and, thus, can be used
# to provide information to the user that might be useful to see at runtime.
logging.addLevelName(35, "HINT")
# NOTE: we also add a custom level DEPRECATED which has an even higher priority.
logging.addLevelName(45, "DEPRECATED")


class _StderrHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """A logging handler hard-coded to `sys.stderr`.

    The reason for explicitly deriving this class, is that Python's `logging.StreamHandler` does not
    respect stream redirection. However, for coBib's TUI this is an important requirement which can
    be achieved by a runtime check of the stream during the `emit` method.
    """

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stderr
        super().emit(record)


def get_stream_handler(
    level: int = logging.WARNING,
) -> logging.StreamHandler:  # type: ignore[type-arg]
    """Returns a basic StreamHandler logging to `sys.stderr`.

    Args:
        level: the logging level of this handler.
    """
    formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")

    handler = _StderrHandler()
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
        from cobib.config import config

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
        line = line.strip()  # noqa: PLW2901
        if line.startswith(f"## [{current_version}]"):
            started = True
        elif line.startswith(f"## [{cached_version}]"):
            break

        if started:
            lines.append(line)

    groups.append(Markdown("\n".join(lines)))

    return Panel(Group(*groups))
