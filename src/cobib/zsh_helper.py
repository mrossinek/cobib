"""CoBib ZSH Helper."""

import inspect
import os

from cobib import commands
from cobib.database import Database


def list_commands():
    """Lists all available subcommands."""
    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_tags():
    """List all available tags in the database."""
    tags = list(Database().keys())
    return tags


def list_filters():
    """Lists all field names available for filtering."""
    filters = set()
    for entry in Database().values():
        filters.update(entry.data.keys())
    return filters


def example_config():
    """Shows the (well-commented) example configuration."""
    root = os.path.abspath(os.path.dirname(__file__))
    with open(root + "/config/example.py", "r") as file:
        return [line.strip() for line in file.readlines()]
