"""coBib's logging module.

This module provides utility methods to set up logging to different handlers.
"""

import logging
import logging.handlers
from pathlib import Path
from sys import stderr
from typing import Optional, Union

from .rel_path import RelPath


def get_stream_handler() -> logging.StreamHandler:
    """Returns a basic StreamHandler logging to `sys.stderr`."""
    formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")

    handler = logging.StreamHandler(stream=stderr)
    handler.setLevel("WARNING")
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
