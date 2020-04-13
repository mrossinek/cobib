"""CoBib ZSH Helper"""

import inspect

from cobib import commands
from cobib.config import set_config


def list_commands(args=None):  # pylint: disable=unused-argument
    """ List all subcommands """
    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_tags(args=None):
    """ List all tags """
    if not args:
        args = {}
    set_config(args.get('config', None))
    bib_data = commands.base_command.Command._read_database()  # pylint: disable=protected-access
    tags = list(bib_data.keys())
    return tags


def list_filters(args=None):
    """ List all filters """
    if not args:
        args = {}
    set_config(args.get('config', None))
    bib_data = commands.base_command.Command._read_database()  # pylint: disable=protected-access
    filters = set()
    for entry in bib_data.values():
        filters.update(entry.data.keys())
    return filters
