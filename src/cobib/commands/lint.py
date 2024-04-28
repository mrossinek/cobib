"""coBib's lint command.

This command allows you to lint your database.
"""

from __future__ import annotations

import argparse
import logging
from io import StringIO

from rich.console import ConsoleRenderable
from rich.text import Text
from typing_extensions import override

from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class LintFormatter(logging.Formatter):
    """A custom logging.Formatter."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Initializes a LintFormatter."""
        super().__init__(*args, **kwargs)

        self.dirty_entries: set[str] = set()

        from cobib.config import config

        self._database_path = RelPath(config.database.file)

        with open(self._database_path.path, "r", encoding="utf-8") as database:
            self._raw_database = database.readlines()

    def format(self, record: logging.LogRecord) -> str:
        """Format's the LogRecord.

        This custom Formatter uses the LogRecord's attributes to determine from which line of the
        raw database a formatting information was raised. The corresponding line number is used in
        conjunction with the actual message of the LogRecord for the formatting.

        Args:
            record: the LogRecord to be formatted.

        Returns:
            A string encoding the LogRecord's information.
        """
        try:
            entry = record.entry  # type: ignore[attr-defined]
            field = record.field  # type: ignore[attr-defined]
            self.dirty_entries.add(entry)
            raw_db = enumerate(self._raw_database)
            _, line = next(raw_db)
            while not line.startswith(entry):
                _, line = next(raw_db)
            while not line.strip().startswith(field):
                line_no, line = next(raw_db)
            return f"{self._database_path}:{line_no+1} {record.getMessage()}"
        except AttributeError:
            return ""


class LintCommand(Command):
    """The lint Command.

    This command can parse the following arguments:

        * `-f`, `--format`: if specified, the database will be formatted to automatically resolve
            all lint messages.
    """

    name = "lint"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self._lint_messages: list[str] = []

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="lint", description="Lint subcommand parser.", exit_on_error=True
        )
        parser.add_argument(
            "-f",
            "--format",
            action="store_true",
            help="Automatically format database to conform with linter.",
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        output = StringIO()

        handler = logging.StreamHandler(output)
        handler.setLevel(logging.INFO)
        handler.addFilter(logging.Filter("cobib.database.entry"))

        formatter = LintFormatter()
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        if root_logger.getEffectiveLevel() > logging.INFO:
            # overwriting all existing handlers with this local one
            root_logger.handlers = [handler]
            root_logger.setLevel(logging.INFO)
        else:
            # appending new handler
            root_logger.addHandler(handler)

        # trigger database reading to cause lint messages upon entry-construction
        Database.read(bypass_cache=True)

        self._lint_messages = output.getvalue().split("\n")

        root_logger.removeHandler(handler)

        if all(not msg for msg in self._lint_messages):
            self._lint_messages = ["Congratulations! Your database triggers no lint messages."]

        elif self.largs.format:
            for label in formatter.dirty_entries:
                # we exploit the rename method to register all dirty entries for re-writing
                Database().rename(label, label)

            Database.save()
            self.git()

            self._lint_messages.insert(
                0, "The following lint messages have successfully been resolved:"
            )

    @override
    def render_porcelain(self) -> list[str]:
        return self._lint_messages

    @override
    def render_rich(self) -> ConsoleRenderable:
        text = Text("\n".join(self._lint_messages))
        return text
