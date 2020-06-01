"""Cobib init command."""

import argparse
import os
import sys

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command


class InitCommand(Command):
    """Init Command."""

    name = 'init'

    def execute(self, args, out=sys.stdout):
        """Initialize database.

        Initializes the yaml database file at the configured location.

        Args: See base class.
        """
        parser = ArgumentParser(prog="init", description="Init subcommand parser.")
        parser.add_argument('-f', '--force', action='store_true',
                            help="force initializtion of database. Warning: this overwrites any " +
                            "existing file!")

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        conf_database = CONFIG.config['DATABASE']
        file = os.path.expanduser(conf_database['file'])
        if os.path.exists(file) and not largs.force:
            print("Database file already exists! Use --force to overwrite.", file=sys.stderr)
            return
        open(file, 'w').close()
