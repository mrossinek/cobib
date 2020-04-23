"""Cobib init command"""

import os
import sys

from cobib.config import CONFIG
from .base_command import Command


class InitCommand(Command):
    """Init Command"""

    name = 'init'

    def execute(self, args, out=sys.stdout):
        """initialize database

        Initializes the yaml database file at the configured location.
        """
        conf_database = dict(CONFIG['DATABASE'])
        file = os.path.expanduser(conf_database['file'])
        open(file, 'w').close()
