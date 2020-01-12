""" CReMa ZSH Helper """

import inspect

from . import crema


def list_commands(args=None):  # pylint: disable=unused-argument
    """ List all subcommands """
    subcommands = []
    for name, member in inspect.getmembers(crema):
        if inspect.isfunction(member) and 'args' in inspect.signature(member).parameters:
            subcommands.append(name[:-1] + ':' + member.__doc__.split('\n')[0])
    return subcommands


def list_tags(args=None):
    """ List all tags """
    if 'config' in args.keys():
        crema.set_config(args['config'])
    else:
        crema.set_config()
    bib_data = crema._read_database()  # pylint: disable=protected-access
    tags = list(bib_data.keys())
    return tags


def list_filters(args=None):
    """ List all filters """
    if 'config' in args.keys():
        crema.set_config(args['config'])
    else:
        crema.set_config()
    bib_data = crema._read_database()  # pylint: disable=protected-access
    filters = set()
    for entry in bib_data.values():
        filters.update(entry.data.keys())
    return filters
