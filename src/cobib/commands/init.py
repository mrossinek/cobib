"""coBib's Init command.

This command must be the first command you ever execute with coBib because it takes care of
initializing the database.
Generally, you will only ever need to run this command once, but it is safe to run it multiple times
(although it will likely have no effect).

To get started with coBib you must run:
```
cobib init
```
This will initialize the database in the location specified by
`cobib.config.config.DatabaseConfig.file`.

If you enabled the automatic git-integration of coBib via `cobib.config.config.DatabaseConfig.git`,
you must initialize this separately via:
```
cobib init --git
```
If you have not run the first command yet, you can directly initialize the database *and* the
git-integration by only running the second command.

.. warning::
   You can**not** run this command from the TUI, because the database must have already been
   initialized *before* you can start the TUI in the first place.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class InitCommand(Command):
    """The Init Command.

    This command can parse the following arguments:

        * `-g`, `--git`: initializes the git-integration.
    """

    name = "init"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.file: Path
        """The path to the database file."""

        self.root: Path
        """The parent directory where the database file resides. This is where the git repository
        gets initialized (if the git integration was enabled)."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="init", description="Init subcommand parser.")
        parser.add_argument("-g", "--git", action="store_true", help="initialize git repository")
        cls.argparser = parser

    @override
    def execute(self) -> None:
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
