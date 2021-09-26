"""coBib's logging module.

This module provides utility methods to set up logging to different handlers.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Union

from pkg_resources import get_distribution

from .rel_path import RelPath


class _StderrHandler(logging.StreamHandler):
    """A logging handler hard-coded to `sys.stderr`.

    The reason for explicitly deriving this class, is that Python's `logging.StreamHandler` does not
    respect stream redirection. However, for coBib's TUI this is an important requirement which can
    be achieved by a runtime check of the stream during the `emit` method.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        self.stream = sys.stderr
        super().emit(record)


def get_stream_handler(level: int = logging.WARNING) -> logging.StreamHandler:
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
    level: Union[str, int] = "INFO", logfile: Optional[Union[str, Path]] = None
) -> logging.handlers.RotatingFileHandler:
    """Returns a `RotatingFileHandler`.

    Args:
        level: the handler's logging level.
        logfile: the output path for the log file.
    """
    if logfile is None:
        # pylint: disable=import-outside-toplevel
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


def print_changelog(version: str, cached_version_path: Optional[str]) -> None:
    """Prints the latest section of the CHANGELOG to stdout.

    This function prints the contents of the CHANGELOG (extracted from the PKG-INFO metadata)
    between the current version (`version`) and the latest cached version (extracted from the
    provided file path).

    Args:
        version: the currently running version of coBib.
        cached_version_path: the path to the file which caches the previously executed version of
            coBib. If `None`, this method exits early (thereby silencing this feature).
    """
    if cached_version_path is None:
        return

    try:
        current_version = version[: version.index("+")]
    except ValueError:
        current_version = version

    cached_version = None
    try:
        with open(RelPath(cached_version_path).path, "r", encoding="utf-8") as version_file:
            cached_version = version_file.read().strip()
    except FileNotFoundError:
        pass

    if current_version == cached_version:
        return

    with open(RelPath(cached_version_path).path, "w", encoding="utf-8") as version_file:
        version_file.write(current_version)

    lines = ["\x1b[1mHi there! It looks like you have updated coBib; here is what's new:\x1b[22m\n"]

    metadata = ""
    try:
        metadata = get_distribution("cobib").get_metadata("METADATA")
    except FileNotFoundError:
        try:
            metadata = get_distribution("cobib").get_metadata("PKG-INFO")
        except FileNotFoundError:
            lines += [
                "I wanted to show you the new changes here but was unable to query ",
                "them from your installation. You can look them up yourself, here: ",
                "https://gitlab.com/mrossinek/cobib/-/blob/master/CHANGELOG.md",
            ]

    num_printed_lines = -1
    for line in metadata.splitlines():
        line = line.strip()
        if line.startswith(f"## [{current_version}]"):
            num_printed_lines = 0
        elif line.startswith(f"## [{cached_version}]"):
            num_printed_lines = -1
        elif num_printed_lines >= 20:
            num_printed_lines = -1
            lines.extend(
                [
                    "\n...\n\x1b[31m",
                    "This output is shortened for the sake of brevity! For more information visit:",
                    "https://gitlab.com/mrossinek/cobib/-/blob/master/CHANGELOG.md",
                ]
            )

        if num_printed_lines >= 0:
            lines.append(line)
            num_printed_lines += 1

    print("\x1b[33m", end="")
    print("\n".join(lines).strip())
    print("\x1b[0m", end="", flush=True)

    input("\nPress Enter to continue...")
