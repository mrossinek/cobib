"""Cobib init command"""

import os

from cobib.config import CONFIG
from .base_command import Command


class InitCommand(Command):  # pylint: disable=too-few-public-methods
    """Init Command"""

    name = 'init'

    def execute(self, args):  # pylint: disable=unused-argument
        """initialize database

        Initializes the yaml database file at the configured location.
        """
        conf_database = dict(CONFIG['DATABASE'])
        file = os.path.expanduser(conf_database['file'])
        open(file, 'w').close()
