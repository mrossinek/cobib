"""Cobib init command."""

import argparse
import logging
import os
import sys

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class InitCommand(Command):
    """Init Command."""

    name = 'init'

    def execute(self, args, out=sys.stdout):
        """Initialize database.

        Initializes the yaml database file at the configured location.

        Args: See base class.
        """
        LOGGER.debug('Starting Init command.')
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
        file = os.path.realpath(os.path.expanduser(conf_database['file']))
        if os.path.exists(file) and not largs.force:
            msg = "Database file already exists! Use --force to overwrite."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return
        LOGGER.debug('Creating path for database file: "%s"', os.path.dirname(file))
        os.makedirs(os.path.dirname(file), exist_ok=True)
        LOGGER.debug('Creating empty database file: "%s"', file)
        open(file, 'w').close()
