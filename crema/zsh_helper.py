""" CReMa ZSH Helper """

import inspect

from . import crema


def list_commands():
    """ List all subcommands """
    subcommands = []
    for name, member in inspect.getmembers(crema):
        if inspect.isfunction(member) and 'args' in inspect.signature(member).parameters:
            subcommands.append(name[:-1])
    return subcommands
