#!/usr/bin/python3
"""CoBib main body"""

# IMPORTS
import argparse
import inspect
import sys

from cobib import commands, zsh_helper
from cobib.config import set_config


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1][0] == '_':
        # zsh helper function called
        zsh_main()
        sys.exit()

    subcommands = [cmd.split(':')[0] for cmd in zsh_helper.list_commands()]
    parser = argparse.ArgumentParser(description="Process input arguments.")
    parser.add_argument("-c", "--config", type=argparse.FileType('r'),
                        help="Alternative config file")
    parser.add_argument('command', help="subcommand to be called", choices=subcommands)
    parser.add_argument('args', nargs=argparse.REMAINDER)

    if len(sys.argv) == 1:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    set_config(args.config)
    subcmd = getattr(commands, args.command.title()+'Command')()
    subcmd.execute(args.args)


def zsh_main():
    """ ZSH main helper """
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
