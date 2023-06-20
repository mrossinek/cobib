"""coBib's UI base class.

This class handles the global command-line options which are available across all commands,
including the TUI.
"""

import argparse
import logging
from abc import abstractmethod
from typing import Any

from cobib.config import config
from cobib.ui.components import ArgumentParser
from cobib.utils.logging import get_file_handler, get_stream_handler

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class UI:
    """The UI base class.

    The following global arguments can be parsed:

        * `-v`, `--verbose`: increase the logging verbosity for every time this argument is given.
        * `-p`, `--porcelain`: switches the output to porcelain mode.
        * `-l`, `--logfile`: provides the path to an alternative logging file, overwriting the
            `cobib.config.config.LoggingConfig.logfile` setting.
        * `-c`, `--config`: provides the path to an alternative configuration file.
    """

    parser: ArgumentParser

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes a UI object.

        The function signature is left purposefully vague to allow arbitrarily complex UI subclasses
        built on top of this.

        Args:
            *args: arbitrary positional arguments.
            **kwargs: arbitrary keyword arguments.
        """
        self.root_logger = logging.getLogger()
        """Provides unified access to the root `logging.Logger`."""

        self._stream_handler = get_stream_handler()

        self.root_logger.setLevel("DEBUG")
        self.root_logger.addHandler(self._stream_handler)

        super().__init__(*args, **kwargs)

    def init_argument_parser(self, **kwargs: Any) -> None:
        """Initializes the `argparse.ArgumentParser` for global command-line arguments.

        This method needs to called by a subclass manually (preferably) during its `__init__`. The
        keyword arguments can be used to add additional information to the `ArgumentParser`, which
        can be used to inject information into the `--help` output.

        Args:
            **kwargs: arbitrary keyword arguments passed on to the `ArgumentParser` constructor.
        """
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
        """A hook to register additional command-line arguments.

        Subclasses can overwrite this method to add additional arguments to the `ArgumentParser`.
        This method is internally called during `init_argument_parser`.
        """

    def parse_args(self) -> argparse.Namespace:
        """Parses the provided command-line arguments.

        This method does not take any arguments because it directly gathers them from the
        command-line.

        Returns:
            The parsed arguments.
        """
        arguments = self.parser.parse_args()

        if arguments.logfile:
            LOGGER.info("Switching to FileHandler logger in %s", arguments.logfile.name)
            file_handler = get_file_handler(
                "DEBUG" if arguments.verbose > 1 else "INFO", logfile=arguments.logfile.name
            )
            self.root_logger.addHandler(file_handler)

        # set logging verbosity level
        if arguments.verbose == 1:
            self._stream_handler.setLevel(logging.INFO)
            LOGGER.info("Logging level set to INFO.")
        elif arguments.verbose > 1:
            self._stream_handler.setLevel(logging.DEBUG)
            LOGGER.info("Logging level set to DEBUG.")

        # load configuration
        config.load(arguments.config)

        return arguments

    @abstractmethod
    def run(self) -> None:
        """Runs the actual UI instance."""
