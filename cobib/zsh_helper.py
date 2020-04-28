"""CoBib ZSH Helper"""

import inspect

from cobib import commands
from cobib.config import CONFIG
from cobib.database import read_database


def list_commands(args=None):  # pylint: disable=unused-argument
    """ List all subcommands """
    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_tags(args=None):
    """ List all tags """
    if not args:
        args = {}
    CONFIG.set_config(args.get('config', None))
    read_database()  # pylint: disable=protected-access
    tags = list(CONFIG.config['BIB_DATA'].keys())
    return tags


def list_filters(args=None):
    """ List all filters """
    if not args:
        args = {}
    CONFIG.set_config(args.get('config', None))
    read_database()  # pylint: disable=protected-access
    filters = set()
    for entry in CONFIG.config['BIB_DATA'].values():
        filters.update(entry.data.keys())
    return filters
