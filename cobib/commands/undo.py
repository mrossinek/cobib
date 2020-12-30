"""CoBib undo command."""

import argparse
import logging
import os
import subprocess
import sys

from cobib.config import CONFIG
from cobib.database import read_database
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class UndoCommand(Command):
    """Undo Command."""

    name = 'undo'

    def execute(self, args, out=sys.stdout):
        """Undo last change.

        Undoes the last change to the database file. By default, only auto-committed changes by
        CoBib will be undone. Use `--force` to undo other changes, too.

        Args: See base class.
        """
        conf_database = CONFIG.config['DATABASE']
        git_tracked = conf_database.getboolean('git')
        if not git_tracked:
            msg = "You must enable CoBib's git-tracking in order to use the `Undo` command. " + \
                "Please refer to the man-page for more information on how to do so."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        file = os.path.realpath(os.path.expanduser(conf_database['file']))
        root = os.path.dirname(file)
        if not os.path.exists(os.path.join(root, '.git')):
            msg = "You have configured, but not initialized CoBib's git-tracking. " + \
                "Please consult `cobib init --help` for more information on how to do so."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        LOGGER.debug('Starting Undo command.')
        parser = ArgumentParser(prog="undo", description="Undo subcommand parser.")
        parser.add_argument("-f", "--force", action='store_true',
                            help="allow undoing non auto-committed changes")

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        LOGGER.debug('Obtaining git log.')
        lines = subprocess.check_output([
            "git", "--no-pager", "-C", f"{root}", "log", "--oneline", "--no-decorate", "--no-abbrev"
        ])
        undone_shas = set()
        for commit in lines.decode().strip().split('\n'):
            LOGGER.debug('Processing commit %s', commit)
            sha, *message = commit.split()
            if message[0] == 'Undo':
                # Store already undone commit sha
                LOGGER.debug('Storing undone commit sha: %s', sha)
                undone_shas.add(message[-1])
                continue
            if sha in undone_shas:
                LOGGER.info('Skipping %s as it was already undone', sha)
                continue
            if largs.force or (message[0] == 'Auto-commit:' and message[-1] != 'InitCommand'):
                # we undo a commit if and only if:
                #  - the `force` argument is specified OR
                #  - the commit is an `auto-committed` change which is NOT from `InitCommand`
                LOGGER.debug('Attempting to undo %s.', sha)
                commands = [
                    f"git -C {root} revert --no-commit {sha}",
                    f"git -C {root} commit --no-gpg-sign --quiet --message 'Undo {sha}'"
                ]
                undo = subprocess.Popen('; '.join(commands), shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                undo.communicate()
                if undo.returncode != 0:
                    LOGGER.error('Undo was unsuccessful. Please consult the logs and git history of'
                                 ' your database for more information.')
                break
        else:
            msg = "Could not find a commit to undo. Please commit something first!"
            print(msg, file=sys.stderr)
            LOGGER.warning(msg)
            sys.exit(1)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Undo command triggered from TUI.')
        tui.execute_command(['undo'], skip_prompt=True)
        # update database list
        LOGGER.debug('Updating list after Undo command.')
        read_database(fresh=True)
        tui.viewport.update_list()
        # if cursor line is below buffer height, move it one line back up
        if tui.STATE.current_line >= tui.viewport.buffer.height:
            tui.STATE.current_line -= 1
