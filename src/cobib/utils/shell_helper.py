"""coBib's shell helpers.

This module provides a variety of shell helper utilities.
"""

import inspect
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

    filters = set()
    for entry in Database().values():
        filters.update(entry.data.keys())
    return filters


def example_config() -> List[str]:
    """Shows the (well-commented) example configuration."""
    root = RelPath(__file__).parent.parent
    with open(root / "config/example.py", "r") as file:
        return [line.strip() for line in file.readlines()]
