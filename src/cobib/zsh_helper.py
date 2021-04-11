"""coBib's ZSH helpers.

This module provides a variety of ZSH helper utilities.
"""

import inspect
from pathlib import Path
from typing import List, Set

from cobib import commands
from cobib.database import Database


def list_commands() -> List[str]:
    """Lists all available subcommands."""
    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_tags() -> List[str]:
    """List all available tags in the database."""
    tags = list(Database().keys())
    return tags


def list_filters() -> Set[str]:
    """Lists all field names available for filtering."""
    filters = set()
    for entry in Database().values():
        filters.update(entry.data.keys())
    return filters


def example_config() -> List[str]:
    """Shows the (well-commented) example configuration."""
    root = Path(__file__).expanduser().resolve().parent
    with open(root / "config/example.py", "r") as file:
        return [line.strip() for line in file.readlines()]
