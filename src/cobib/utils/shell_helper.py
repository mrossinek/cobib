"""coBib's shell helpers.

This module provides a variety of shell helper utilities.
"""

import inspect
import logging
from io import StringIO
from typing import List, Set

from .rel_path import RelPath


def list_commands() -> List[str]:
    """Lists all available subcommands."""
    # pylint: disable=import-outside-toplevel
    from cobib import commands

    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_labels() -> List[str]:
    """List all available labels in the database."""
    # pylint: disable=import-outside-toplevel
    from cobib.database import Database

    labels = list(Database().keys())
    return labels


def list_filters() -> Set[str]:
    """Lists all field names available for filtering."""
    # pylint: disable=import-outside-toplevel
    from cobib.database import Database

    filters: Set[str] = {"ID"}
    for entry in Database().values():
        filters.update(entry.data.keys())
    return filters


def example_config() -> List[str]:
    """Shows the (well-commented) example configuration."""
    root = RelPath(__file__).parent.parent
    with open(root / "config/example.py", "r") as file:
        return [line.strip() for line in file.readlines()]


class LintFormatter(logging.Formatter):
    """A custom logging.Formatter."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        # noqa: D107
        super().__init__(*args, **kwargs)

        # pylint: disable=import-outside-toplevel
        from cobib.config import config

        self._database_path = RelPath(config.database.file)

        with open(self._database_path.path, "r") as database:
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
            raw_db = enumerate(self._raw_database)
            _, line = next(raw_db)
            while not line.startswith(entry):
                _, line = next(raw_db)
            while not line.strip().startswith(field):
                line_no, line = next(raw_db)
            return f"{self._database_path}:{line_no+1} {record.getMessage()}"
        except AttributeError:
            return ""


def lint_database() -> List[str]:
    """Lints the users database."""
    # pylint: disable=import-outside-toplevel
    from cobib.database import Database

    output = StringIO()

    handler = logging.StreamHandler(output)
    handler.setLevel(logging.INFO)
    handler.addFilter(logging.Filter("cobib.database.entry"))
    handler.setFormatter(LintFormatter())

    root_logger = logging.getLogger()
    if root_logger.getEffectiveLevel() > logging.INFO:
        # overwriting all existing handlers with this local one
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.INFO)
    else:
        # appending new handler
        root_logger.addHandler(handler)

    # trigger database reading to cause lint messages upon entry-construction
    Database.read()

    lint_messages = output.getvalue().split("\n")

    root_logger.removeHandler(handler)

    if all(not msg for msg in lint_messages):
        return ["Congratulations! Your database triggers no lint messages."]
    return lint_messages
