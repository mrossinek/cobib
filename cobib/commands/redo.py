"""CoBib redo command."""

import argparse
import logging
import os
import subprocess
import sys

from cobib.config import config
from cobib.database import Database
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class RedoCommand(Command):
    """Redo Command."""

    name = 'redo'

    def execute(self, args, out=sys.stdout):
        """Redo last undone change.

        Redoes the last undone change to the database file.

        Args: See base class.
        """
        git_tracked = config.database.git
        if not git_tracked:
            msg = "You must enable CoBib's git-tracking in order to use the `Redo` command. " + \
                "Please refer to the man-page for more information on how to do so."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        file = os.path.realpath(os.path.expanduser(config.database.file))
        root = os.path.dirname(file)
        if not os.path.exists(os.path.join(root, '.git')):
            msg = "You have configured, but not initialized CoBib's git-tracking. " + \
                "Please consult `cobib init --help` for more information on how to do so."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        LOGGER.debug('Starting Redo command.')
        parser = ArgumentParser(prog="redo", description="Redo subcommand parser.")

        try:
            # pylint: disable=unused-variable
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        LOGGER.debug('Obtaining git log.')
        lines = subprocess.check_output([
            "git", "--no-pager", "-C", f"{root}", "log", "--oneline", "--no-decorate", "--no-abbrev"
        ])
        redone_shas = set()
        for commit in lines.decode().strip().split('\n'):
            LOGGER.debug('Processing commit %s', commit)
            sha, *message = commit.split()
            if message[0] == 'Redo':
                # Store already redone commit sha
                LOGGER.debug('Storing undone commit sha: %s', sha)
                redone_shas.add(message[-1])
                continue
            if sha in redone_shas:
                LOGGER.info('Skipping %s as it was already redone', sha)
                continue
            if message[0] == 'Undo':
                LOGGER.debug('Attempting to redo %s.', sha)
                commands = [
                    f"git -C {root} revert --no-commit {sha}",
                    f"git -C {root} commit --no-gpg-sign --quiet --message 'Redo {sha}'"
                ]
                redo = subprocess.Popen('; '.join(commands), shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                redo.communicate()
                if redo.returncode != 0:
                    LOGGER.error('Redo was unsuccessful. Please consult the logs and git history of'
                                 ' your database for more information.')
                break
        else:
            msg = "Could not find a commit to redo. You must have undone something first!"
            print(msg, file=sys.stderr)
            LOGGER.warning(msg)
            sys.exit(1)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Redo command triggered from TUI.')
        tui.execute_command(['redo'], skip_prompt=True)
        # update database list
        LOGGER.debug('Updating list after Redo command.')
        Database().read()
        tui.viewport.update_list()
        # if cursor line is below buffer height, move it one line back up
        if tui.STATE.current_line >= tui.viewport.buffer.height:
            tui.STATE.current_line -= 1
