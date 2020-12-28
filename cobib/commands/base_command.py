"""CoBib Command interface."""

import argparse
import json
import logging
import os
import shlex
import sys
from abc import ABC, abstractmethod

from cobib.config import CONFIG

LOGGER = logging.getLogger(__name__)


class Command(ABC):
    """The Command interface declares a method for command execution and some helper methods."""

    name = 'base'

    @abstractmethod
    def execute(self, args, out=sys.stdout):
        """Command execution.

        Args:
            args (dict): additional arguments used for the execution.
            out (stream, optional): possible alternative to stdout.
        """

    @staticmethod
    def tui(tui):
        """TUI command interface.

        Args:
            tui (cobib.TUI): instance of CoBib's TUI.
        """

    def git(self, args=None, force=False):
        """Track command's changes with git.

        Args:
            args (optional, dict): a dictionary containing the command arguments.
            force (boolean): whether to ignore the configuration setting.
        """
        conf_database = CONFIG.config['DATABASE']
        git_tracked = conf_database.getboolean('git')
        if not git_tracked and not force:
            return

        file = os.path.realpath(os.path.expanduser(conf_database['file']))
        root = os.path.dirname(file)

        if not os.path.exists(os.path.join(root, '.git')):
            if git_tracked:
                msg = 'You have configured CoBib to track your database with git. ' + \
                      'Please run `cobibt init --git`, to initialize this tracking.'
                print(msg, file=sys.stderr)
                LOGGER.warning(msg)
                return

        msg = f"Auto-commit: {self.name.title()}Command"
        if args:
            msg += '\n\n'
            msg += json.dumps(args, indent=2, default=str)

        commands = [
            f'cd {root}',
            f'git add -- {file}',
            f'git commit --no-gpg-sign --quiet --message {shlex.quote(msg)}',
        ]
        LOGGER.debug('Auto-commit to git from %s command.', self.name)
        os.system('; '.join(commands))


class ArgumentParser(argparse.ArgumentParser):
    """Overwrite ArgumentParser to allow catching any error messages thrown by parse_args.

    Source: https://stackoverflow.com/a/5943381
    """

    def _get_action_from_name(self, name):
        """Given a name, get the Action instance registered with this parser.

        If only it were made available in the ArgumentError object. It is
        passed as it's first argument...

        Args:
            name (str or None): name of the action.
        """
        container = self._actions
        if name is None:
            return None
        for action in container:
            if '/'.join(action.option_strings) == name:
                return action
            if action.metavar == name:
                return action
            if action.dest == name:
                return action
        return None

    def error(self, message):
        """Prints an error.

        Args:
            message (str): error message string.
        """
        exc = sys.exc_info()[1]
        if exc:
            raise exc
        super().error(message)
