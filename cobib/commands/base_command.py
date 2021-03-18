"""CoBib Command interface."""

import argparse
import json
import logging
import os
import shlex
import sys
from abc import ABC, abstractmethod

from cobib.config import config

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
            tui (cobib.tui.TUI): instance of CoBib's TUI.
        """

    def git(self, args=None, force=False):
        """Track command's changes with git.

        Args:
            args (optional, dict): a dictionary containing the command arguments.
            force (boolean): whether to ignore the configuration setting.
        """
        git_tracked = config.database.git
        if not git_tracked and not force:
            return

        file = os.path.realpath(os.path.expanduser(config.database.file))
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
    """Overwrite ArgumentParser to allow catching any error messages thrown by parse_args."""
    # TODO: once Python 3.9 becomes the default, make use of the exit_on_error argument.
    # Source: https://docs.python.org/3/library/argparse.html#exit-on-error

    def exit(self, status=0, message=None):
        """Overwrite the exit method to raise an error instead."""
        if status:
            raise argparse.ArgumentError(None, f'Error: {message}')
        super().exit(status, message)
