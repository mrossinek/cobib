"""CoBib ZSH Helper."""

import inspect

from cobib import commands
from cobib.config import CONFIG
from cobib.database import read_database


def list_commands(args=None):  # pylint: disable=unused-argument
    """List all subcommands.

    Args:
        args (dict, optional): unused but necessary due to the function template.

    Returns:
        A list of all available subcommands.
    """
    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_tags(args=None):
    """List all tags.

    Args:
        args (dict, optional): dictionary of keyword arguments.

    Returns:
        A list of all available tags in the database.
    """
    if not args:
        args = {}
    CONFIG.set_config(args.get('config', None))
    read_database()
    tags = list(CONFIG.config['BIB_DATA'].keys())
    return tags


def list_filters(args=None):
    """List all filters.

    Args:
        args (dict, optional): dictionary of keyword arguments.

    Returns:
        A list of all field names available for filtering.
    """
    if not args:
        args = {}
    CONFIG.set_config(args.get('config', None))
    read_database()
    filters = set()
    for entry in CONFIG.config['BIB_DATA'].values():
        filters.update(entry.data.keys())
    return filters
