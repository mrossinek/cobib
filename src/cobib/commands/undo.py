"""coBib's Undo command.

This command can be used to undo the changes of the a previous command.
```
cobib undo
```
For obvious reasons, this will only undo commands which had an effect on the contents of the
database file.
Moreover, as a safety measure, this command will only undo those changes, which have been committed
by coBib *automatically*.
You can disable this be setting the `--force` argument which *always* undoes the last commit:
```
cobib undo --force
```

.. warning::
   This command is *only* available if coBib's git-integration has been enabled via
   `cobib.config.config.DatabaseConfig.git` *and* initialized properly (see `cobib.commands.init`).

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `u` key.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class UndoCommand(Command):
    """The Undo Command.

    This command can parse the following arguments:

        * `-f`, `--force`: if specified, this will also revert changes which have *not* been
          auto-committed by coBib.
    """

    name = "undo"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.root: Path
        """The path to the root of the git repository tracking the database."""

        self.sha: str
        """The git commit SHA which was reverted by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="undo", description="Undo subcommand parser.")
        parser.add_argument(
            "-f", "--force", action="store_true", help="allow undoing non auto-committed changes"
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        git_tracked = config.database.git
        if not git_tracked:
            msg = (
                "You must enable coBib's git-tracking in order to use the `Undo` command."
                "\nPlease refer to the documentation for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        file = RelPath(config.database.file).path
        self.root = file.parent
        if not (self.root / ".git").exists():
            msg = (
                "You have configured, but not initialized coBib's git-tracking."
                "\nPlease consult `cobib init --help` for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        LOGGER.debug("Starting Undo command.")

        Event.PreUndoCommand.fire(self)

        LOGGER.debug("Obtaining git log.")
        lines = subprocess.check_output(
            [
                "git",
                "--no-pager",
                "-C",
                f"{self.root}",
                "log",
                "--oneline",
                "--no-decorate",
                "--no-abbrev",
            ]
        )
        undone_shas = set()
        for commit in lines.decode().strip().split("\n"):
            LOGGER.debug("Processing commit %s", commit)
            self.sha, *message = commit.split()
            if message[0] == "Undo":
                # Store already undone commit sha
                LOGGER.debug("Storing undone commit sha: %s", message[-1])
                undone_shas.add(message[-1])
                continue
            if self.sha in undone_shas:
                LOGGER.info("Skipping %s as it was already undone", self.sha)
                continue
            if self.largs.force or (message[0] == "Auto-commit:" and message[-1] != "InitCommand"):
                # we undo a commit if and only if:
                #  - the `force` argument is specified OR
                #  - the commit is an `auto-committed` change which is NOT from `InitCommand`
                LOGGER.debug("Attempting to undo %s.", self.sha)
                commands = [
                    f"git -C {self.root} revert --no-commit {self.sha}",
                    f"git -C {self.root} commit --no-gpg-sign --quiet --message 'Undo {self.sha}'",
                ]
                with subprocess.Popen(
                    "; ".join(commands), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                ) as undo:
                    undo.communicate()
                    if undo.returncode != 0:
                        LOGGER.error(  # pragma: no cover
                            "Undo was unsuccessful. Please consult the logs and git history of your"
                            " database for more information."
                        )
                    else:
                        # update Database
                        Database().read()
                break
        else:
            msg = "Could not find a commit to undo. Please commit something first!"
            LOGGER.warning(msg)
            sys.exit(1)

        Event.PostUndoCommand.fire(self)
