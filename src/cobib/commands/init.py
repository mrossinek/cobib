"""coBib's Init command.

This command must be the first command you ever execute with coBib because it takes care of
initializing the database.
Generally, you will only ever need to run this command once, but it is safe to run it multiple times
(although it will likely have no effect).

To get started with coBib you must run:
```
cobib init
```
This will initialize the database in the location specified by `config.database.file`.

If you enabled the automatic git-integration of coBib via `config.database.git`, you must initialize
this separately via:
```
cobib init --git
```
If you have not run the first command yet, you can directly initialize the database *and* the
git-integration by only running the second command.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List

from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class InitCommand(Command):
    """The Init Command."""

    name = "init"

    def __init__(self, args: List[str]) -> None:
        """TODO."""
        super().__init__(args)

        self.file: Path
        self.root: Path

    @classmethod
    def init_argparser(cls) -> None:
        """TODO."""
        parser = ArgumentParser(prog="init", description="Init subcommand parser.")
        parser.add_argument("-g", "--git", action="store_true", help="initialize git repository")
        cls.argparser = parser

    def execute(self) -> None:
        """Initializes the database.

        Initializes the YAML database in the location specified by `config.database.file`.
        If you enabled `config.database.git` *and* you specify the `--git` command-line argument,
        the git-integration will be initialized, too.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `-g`, `--git`: initializes the git-integration.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Init command.")

        Event.PreInitCommand.fire(self)

        self.file = RelPath(config.database.file).path
        self.root = self.file.parent

        file_exists = self.file.exists()
        git_tracked = (self.root / ".git").exists()

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
            open(self.file, "w", encoding="utf-8").close()  # pylint: disable=consider-using-with

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
                msg = (
                    "In order to use git you must configure your name and email first! For more "
                    "information please consult `man gittutorial`."
                )
                LOGGER.warning(msg)
                sys.exit(1)
            LOGGER.debug('Initializing git repository in "%s"', self.root)
            os.system(f"git init {self.root}")
            self.git(force=True)

        Event.PostInitCommand.fire(self)
