"""coBib's logging module.

This module provides utility methods to set up logging to different handlers.
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional, Union

from .rel_path import RelPath


def log_to_stream(level: Union[str, int] = "WARNING") -> None:
    """Configures a `StreamHandler` logger.

    Args:
        level: verbosity level indicator.
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s [%(levelname)s] %(name)s %(funcName)s:%(lineno)d %(message)s"
                    )
                },
            },
            "handlers": {
                "default": {
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": level,
                    "formatter": "standard",
                    "propagate": True,
                }
            },
        }
    )


def log_to_file(
    level: Union[str, int] = "INFO", logfile: Optional[Union[str, Path]] = None
) -> None:
    """Configures a `RotatingFileHandler` logger.

    Args:
        level: verbosity level indicator.
        logfile: output path for log file.
    """
    if logfile is None:
        # pylint: disable=import-outside-toplevel
        from cobib.config import config

        logfile = config.logging.logfile

    path = RelPath(logfile).path
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s [%(levelname)s] %(name)s %(funcName)s:%(lineno)d %(message)s"
                    )
                },
            },
            "handlers": {
                "default": {
                    "formatter": "standard",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": path,
                    "maxBytes": 10485760,  # 10 Megabytes
                    "backupCount": 10,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": level,
                    "formatter": "standard",
                    "propagate": True,
                }
            },
        }
    )
