#!/usr/bin/python3
from crema import crema

import argparse
import configparser
import os
import sys

# global config
# the default configuration file will be loaded from ~/.config/crema/config.ini
CONFIG = configparser.ConfigParser()


def main():
    subcommands = crema._list_commands()
    parser = argparse.ArgumentParser(description="Process input arguments.")
    parser.add_argument("-c", "--config", type=argparse.FileType('r'),
                        help="Alternative config file")
    parser.add_argument('command', help="subcommand to be called",
                        choices=subcommands)
    parser.add_argument('args', nargs=argparse.REMAINDER)

    if (len(sys.argv) == 1):
        parser.print_usage(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.config is not None:
        CONFIG.read(args.config.name)
    else:
        CONFIG.read(os.path.expanduser('~/.config/crema/config.ini'))

    crema._load_config(CONFIG)
    subcmd = getattr(crema, args.command+'_')
    subcmd(args.args)


if __name__ == '__main__':
    main()
