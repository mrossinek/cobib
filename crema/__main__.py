#!/usr/bin/python3
"""CReMa main body"""

# IMPORTS
import argparse
import configparser
import os
import sys

from . import crema

# global config
# the configuration file will be loaded from ~/.config/crema/config.ini
# if this file does not exists, defaults are taken from the package data config
CONFIG = configparser.ConfigParser()


def main():
    """Main function"""
    subcommands = crema._list_commands()
    parser = argparse.ArgumentParser(description="Process input arguments.")
    parser.add_argument("-c", "--config", type=argparse.FileType('r'),
                        help="Alternative config file")
    parser.add_argument('command', help="subcommand to be called",
                        choices=subcommands)
    parser.add_argument('args', nargs=argparse.REMAINDER)

    if len(sys.argv) == 1:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.config is not None:
        CONFIG.read(args.config.name)
    elif os.path.exists('~/.config/crema/config.ini'):
        CONFIG.read(os.path.expanduser('~/.config/crema/config.ini'))
    else:
        root = os.path.abspath(os.path.dirname(__file__))
        CONFIG.read(os.path.join(root, 'docs', 'default.ini'))

    crema._load_config(CONFIG)
    subcmd = getattr(crema, args.command+'_')
    subcmd(args.args)


if __name__ == '__main__':
    main()
