"""TODO."""

import argparse
import logging
from typing import Any

from cobib.config import config
from cobib.ui.argument_parser import ArgumentParser
from cobib.utils.logging import get_file_handler, get_stream_handler

LOGGER = logging.getLogger(__name__)


class UI:
    """TODO."""

    parser: ArgumentParser

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """TODO."""
        # initialize logging
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel("DEBUG")
        self.stream_handler = get_stream_handler()
        self.root_logger.addHandler(self.stream_handler)

        super().__init__(*args, **kwargs)

    def init_argument_parser(self, **kwargs: Any) -> None:
        """TODO."""
        self.parser = ArgumentParser(**kwargs)
        self.parser.add_argument("-v", "--verbose", action="count", default=0)
        self.parser.add_argument(
            "-p",
            "--porcelain",
            action="store_true",
            help="switches the output to porcelain mode (meant for parsing/testing)",
        )
        self.parser.add_argument(
            "-l", "--logfile", type=argparse.FileType("w"), help="Alternative log file"
        )
        self.parser.add_argument(
            "-c", "--config", type=argparse.FileType("r"), help="Alternative config file"
        )
        self.add_extra_parser_arguments()

    def add_extra_parser_arguments(self) -> None:
        """TODO."""

    def parse_args(self) -> argparse.Namespace:
        """TODO."""
        arguments = self.parser.parse_args()

        if arguments.logfile:
            LOGGER.info("Switching to FileHandler logger in %s", arguments.logfile.name)
            file_handler = get_file_handler(
                "DEBUG" if arguments.verbose > 1 else "INFO", logfile=arguments.logfile.name
            )
            self.root_logger.addHandler(file_handler)

        # set logging verbosity level
        if arguments.verbose == 1:
            self.stream_handler.setLevel(logging.INFO)
            LOGGER.info("Logging level set to INFO.")
        elif arguments.verbose > 1:
            self.stream_handler.setLevel(logging.DEBUG)
            LOGGER.info("Logging level set to DEBUG.")

        # load configuration
        config.load(arguments.config)

        return arguments
