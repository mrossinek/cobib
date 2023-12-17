"""coBib's Importer interface."""

from __future__ import annotations

import argparse
import logging
import sys
from abc import ABC, abstractmethod

from cobib.database import Entry
from cobib.ui.components import ArgumentParser as ArgumentParser  # noqa: PLC0414

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class Importer(ABC):
    """The Importer interface.

    This interface should be implemented by all concrete importer implementations.
    """

    name = "base"
    """The importers `name` is used to register itself as an input argument to the
    `cobib.commands.import_.ImportCommand`."""

    argparser: ArgumentParser
    """Every importer has its own `argparse.ArgumentParser` which is used to parse the arguments
    provided to it."""

    def __init__(self, *args: str, skip_download: bool = False) -> None:
        """Initializes an importer instance.

        Args:
            *args: the sequence of additional importer arguments. These will be passed on to the
                `argparser` of this importer for further parsing.
            skip_download: whether or not to skip downloading of additional files such as attached
                PDF files or notes.
        """
        self.args: tuple[str, ...] = args
        """The raw provided importer arguments."""

        self.largs: argparse.Namespace = self.__class__._parse_args(args)
        """The parsed (local) arguments."""

        self.skip_download = skip_download
        """Whether or not to skip downloading of additional files such as attached PDF files or
        notes."""

    @classmethod
    @abstractmethod
    def init_argparser(cls) -> None:
        """Initializes this importer's `argparse.ArgumentParser`.

        This method needs to be overwritten by every subclass and handles the registration of all
        available importer arguments.
        """

    @classmethod
    def _get_argparser(cls) -> ArgumentParser:
        """Returns this importer's `argparse.ArgumentParser`.

        The reason for having this method is to handle the parser initialization such that it only
        needs to be done once.

        Returns:
            This importer's initialized `argparser` object.
        """
        if hasattr(cls, "argparser"):
            return cls.argparser

        cls.init_argparser()
        return cls.argparser

    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        """Parses the provided importer arguments.

        Args:
            args: the sequence of additional importer arguments provided to the importer upon
                initialization.

        Returns:
            The parsed arguments namespace.
        """
        try:
            largs = cls._get_argparser().parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            sys.exit(1)

        return largs

    @abstractmethod
    async def fetch(self) -> list[Entry]:
        """Fetches the data from the source which this importer links to.

        Returns:
            A list of entries.
        """
