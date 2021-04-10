"""coBib's logging module.

This module provides utility methods to set up logging to different handlers.
"""

import logging
import logging.config
import os

from cobib.config import config


def log_to_stream(level: str = "WARNING") -> None:
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


def log_to_file(level: str = "INFO", logfile: str = config.logging.logfile) -> None:
    """Configures a `RotatingFileHandler` logger.

    Args:
        level: verbosity level indicator.
        logfile: output path for log file.
    """
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
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
                    "filename": logfile,
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
