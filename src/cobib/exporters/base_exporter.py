"""coBib's Exporter interface."""

from __future__ import annotations

import argparse
import logging
import sys
from abc import ABC, abstractmethod

from cobib.database import Entry

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class Exporter(ABC):
    """The Exporter interface.

    This interface should be implemented by all concrete exporter implementations.
    """

    name = "base"
    """The exporters `name` is used to register itself as an input argument to the
    `cobib.commands.export.ExportCommand`."""

    argparser: argparse.ArgumentParser
    """Every exporter has its own `argparse.ArgumentParser` which is used to parse the arguments
    provided to it."""

    def __init__(self, *args: str) -> None:
        """Initializes an exporter instance.

        Args:
            *args: the sequence of additional exporter arguments. These will be passed on to the
                `argparser` of this exporter for further parsing.
        """
        self.args: tuple[str, ...] = args
        """The raw provided exporter arguments."""

        self.largs: argparse.Namespace = self.__class__._parse_args(args)
        """The parsed (local) arguments."""

        self.exported_entries: list[Entry] = []
        """The list of `cobib.database.Entry` objects which will be exported by this exporter."""

    @classmethod
    @abstractmethod
    def init_argparser(cls) -> None:
        """Initializes this exporter's `argparse.ArgumentParser`.

        This method needs to be overwritten by every subclass and handles the registration of all
        available exporter arguments.
        """

    @classmethod
    def _get_argparser(cls) -> argparse.ArgumentParser:
        """Returns this exporter's `argparse.ArgumentParser`.

        The reason for having this method is to handle the parser initialization such that it only
        needs to be done once.

        Returns:
            This exporter's initialized `argparser` object.
        """
        if hasattr(cls, "argparser"):
            return cls.argparser

        cls.init_argparser()
        return cls.argparser

    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        """Parses the provided exporter arguments.

        Args:
            args: the sequence of additional exporter arguments provided to the exporter upon
                initialization.

        Returns:
            The parsed arguments namespace.
        """
        try:
            largs = cls._get_argparser().parse_args(args)
        except argparse.ArgumentError as exc:  # pragma: no cover
            LOGGER.error(exc.message)  # pragma: no cover
            sys.exit(1)

        return largs

    @abstractmethod
    def write(self, entries: list[Entry]) -> None:
        """Writes the data of the provided entries to this exporter's output.

        Args:
            entries: the entries whose data to export.
        """
