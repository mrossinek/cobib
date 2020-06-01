#!/usr/bin/python3
"""CoBib main body."""

import argparse
import inspect
import sys

from cobib import commands, zsh_helper
from cobib import __version__
from cobib.config import CONFIG
from cobib.database import read_database
from cobib.tui import tui


def main():
    """Main executable.

    CoBib's main function used to parse optional keyword arguments and subcommands.
    """
    if len(sys.argv) > 1 and any([a[0] == '_' for a in sys.argv]):
        # zsh helper function called
        zsh_main()
        sys.exit()

    subcommands = [cmd.split(':')[0] for cmd in zsh_helper.list_commands()]
    parser = argparse.ArgumentParser(prog='CoBib', description="""
                                     Cobib input arguments.
                                     If no arguments are given, the TUI will start as a default.
                                     """)
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s v{}".format(__version__))
    parser.add_argument("-c", "--config", type=argparse.FileType('r'),
                        help="Alternative config file")
    parser.add_argument('command', help="subcommand to be called", choices=subcommands, nargs='?')
    parser.add_argument('args', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    CONFIG.set_config(args.config)
    if args.command == 'init':
        # the database file may not exist yet, thus we ensure to execute the command before trying
        # to read the database file
        subcmd = getattr(commands, 'InitCommand')()
        subcmd.execute(args.args)
        return

    read_database()
    if not args.command:
        tui()
    else:
        subcmd = getattr(commands, args.command.title()+'Command')()
        subcmd.execute(args.args)


def zsh_main():
    """ZSH helper.

    Main function used by the ZSH completion script.
    """
    helper_avail = ['_'+m[0] for m in inspect.getmembers(zsh_helper) if inspect.isfunction(m[1])]
    parser = argparse.ArgumentParser(description="Process ZSH helper call")
    parser.add_argument('helper', help="zsh helper to be called", choices=helper_avail)
    parser.add_argument('args', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    helper = getattr(zsh_helper, args.helper.strip('_'))
    # any zsh helper function will return a list of the requested items
    for item in helper(args=args.args):
        print(item)


if __name__ == '__main__':
    main()
