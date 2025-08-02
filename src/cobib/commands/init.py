"""Initialize a database.

.. include:: ../man/cobib-init.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from typing_extensions import override

from cobib.config import Event, config
from cobib.utils.git import is_inside_work_tree
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class InitCommand(Command):
    """The Init Command.

    This command can parse the following arguments:

        * `-g`, `--git`: initializes the git-integration.
    """

    name = "init"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.file: Path
        """The path to the database file."""

        self.root: Path
        """The parent directory where the database file resides. This is where the git repository
        gets initialized (if the git integration was enabled)."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="init", description="Init subcommand parser.", exit_on_error=True
        )
        parser.add_argument("-g", "--git", action="store_true", help="initialize git repository")
        cls.argparser = parser

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Init command.")

        Event.PreInitCommand.fire(self)

        self.file = RelPath(config.database.file).path
        self.root = self.file.parent

        file_exists = self.file.exists()
        git_tracked = is_inside_work_tree(self.root)

        if file_exists:
            if git_tracked:
                msg = (
                    "Database file already exists and is being tracked by git. There is nothing "
                    "else to do."
                )
                LOGGER.info(msg)
                return

            if not git_tracked and not self.largs.git:
                msg = "Database file already exists! Use --git to start tracking it with git."
                LOGGER.warning(msg)
                return

        else:
            LOGGER.debug('Creating path for database file: "%s"', self.root)
            self.root.mkdir(parents=True, exist_ok=True)

            LOGGER.debug('Creating empty database file: "%s"', self.file)
            open(self.file, "w", encoding="utf-8").close()

        if self.largs.git:
            if not config.database.git:
                msg = (
                    "You are about to initialize the git tracking of your database, but this will "
                    "only have effect if you also enable the DATABASE/git setting in your "
                    "configuration file!"
                )
                LOGGER.warning(msg)
            # First, check whether git is configured correctly.
            print("Checking `git config --get user.name`:", end=" ", flush=True)
            name_set = os.system("git config --get user.name")
            print()
            print("Checking `git config --get user.email`:", end=" ", flush=True)
            email_set = os.system("git config --get user.email")
            print()
            if name_set != 0 or email_set != 0:
                msg = (  # pragma: no cover
                    "In order to use git you must configure your name and email first! For more "
                    "information please consult `man gittutorial`."
                )
                LOGGER.warning(msg)  # pragma: no cover
                sys.exit(1)
            LOGGER.debug('Initializing git repository in "%s"', self.root)
            os.system(f"git init {self.root}")
            self.git(force=True)

        Event.PostInitCommand.fire(self)
