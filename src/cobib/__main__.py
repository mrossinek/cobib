#!/usr/bin/env python3
"""coBib main body."""

import argparse
import inspect
import logging
import sys

from cobib import __version__, commands, zsh_helper
from cobib.config import config
from cobib.database import Database
from cobib.logging import log_to_file, log_to_stream
from cobib.tui import tui

LOGGER = logging.getLogger(__name__)


def main():
    """Main executable.

    coBib's main function used to parse optional keyword arguments and subcommands.
    """
    if len(sys.argv) > 1 and any(a[0] == "_" for a in sys.argv):
        # zsh helper function called
        zsh_main()
        sys.exit()

    # initialize logging
    log_to_stream()

    subcommands = [cmd.split(":")[0] for cmd in zsh_helper.list_commands()]
    parser = argparse.ArgumentParser(
        prog="coBib",
        description=(
            "Cobib input arguments.\nIf no arguments are given, the TUI will start as a default."
        ),
    )
    parser.add_argument("--version", action="version", version="%(prog)s v{}".format(__version__))
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-l", "--logfile", type=argparse.FileType("w"), help="Alternative log file")
    parser.add_argument(
        "-c", "--config", type=argparse.FileType("r"), help="Alternative config file"
    )
    parser.add_argument("command", help="subcommand to be called", choices=subcommands, nargs="?")
    parser.add_argument("args", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.logfile:
        LOGGER.info("Switching to FileHandler logger in %s", args.logfile.name)
        log_to_file("DEBUG" if args.verbose > 1 else "INFO", logfile=args.logfile.name)

    # set logging verbosity level
    if args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
        LOGGER.info("Logging level set to INFO.")
    elif args.verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)
        LOGGER.info("Logging level set to DEBUG.")

    # load configuration
    config.load(args.config)

    if args.command == "init":
        # the database file may not exist yet, thus we ensure to execute the command before trying
        # to read the database file
        subcmd = getattr(commands, "InitCommand")()
        subcmd.execute(args.args)
        return

    # initialize database
    Database()

    if not args.command:
        if args.logfile is None:
            LOGGER.info('Switching to FileHandler logger in "%s"', config.logging.logfile)
            log_to_file("DEBUG" if args.verbose > 1 else "INFO")
        else:
            LOGGER.info(
                'Already logging to "%s". NOT switching to "%s"',
                args.logfile,
                config.logging.logfile,
            )
        tui()
    else:
        subcmd = getattr(commands, args.command.title() + "Command")()
        subcmd.execute(args.args)


def zsh_main():
    """ZSH helper.

    Main function used by the ZSH completion script.
    """
    available_helpers = [
        "_" + m[0] for m in inspect.getmembers(zsh_helper) if inspect.isfunction(m[1])
    ]
    parser = argparse.ArgumentParser(description="Process ZSH helper call")
    parser.add_argument("helper", help="zsh helper to be called", choices=available_helpers)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("-l", "--logfile", type=argparse.FileType("w"), help="Alternative log file")
    parser.add_argument(
        "-c", "--config", type=argparse.FileType("r"), help="Alternative config file"
    )

    args = parser.parse_args()

    if args.logfile:
        LOGGER.info("Switching to FileHandler logger in %s", args.logfile.name)
        log_to_file("DEBUG" if args.verbose > 1 else "INFO", logfile=args.logfile.name)

    # set logging verbosity level
    if args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
        LOGGER.info("Logging level set to INFO.")
    elif args.verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)
        LOGGER.info("Logging level set to DEBUG.")

    # load configuration
    config.load(args.config)
    # initialize database
    Database()

    helper = getattr(zsh_helper, args.helper.strip("_"))
    # any zsh helper function will return a list of the requested items
    for item in helper():
        print(item)


if __name__ == "__main__":
    main()
