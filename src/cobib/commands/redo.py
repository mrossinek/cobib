"""coBib's Redo command.

This command can be used to re-apply the changes *of a previously undone* command (see
`cobib.commands.undo`):
```
cobib redo
```
This command takes *no* additional arguments!

Note, that if you have not used `cobib undo` previously, this command will have no effect!

.. warning::
   This command is *only* available if coBib's git-integration has been enabled via
   `cobib.config.config.DatabaseConfig.git` *and* initialized properly (see `cobib.commands.init`).

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `r` key.
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


class RedoCommand(Command):
    """The Redo Command.

    This command does not parse any additional arguments.
    """

    name = "redo"

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
        parser = ArgumentParser(prog="redo", description="Redo subcommand parser.")
        cls.argparser = parser

    @override
    def execute(self) -> None:
        git_tracked = config.database.git
        if not git_tracked:
            msg = (
                "You must enable coBib's git-tracking in order to use the `Redo` command."
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

        LOGGER.debug("Starting Redo command.")

        Event.PreRedoCommand.fire(self)

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
        redone_shas = set()
        for commit in lines.decode().strip().split("\n"):
            LOGGER.debug("Processing commit %s", commit)
            self.sha, *message = commit.split()
            if message[0] == "Redo":
                # Store already redone commit sha
                LOGGER.debug("Storing redone commit sha: %s", message[-1])
                redone_shas.add(message[-1])
                continue
            if self.sha in redone_shas:
                LOGGER.info("Skipping %s as it was already redone", self.sha)
                continue
            if message[0] == "Undo":
                LOGGER.debug("Attempting to redo %s.", self.sha)
                commands = [
                    f"git -C {self.root} revert --no-commit {self.sha}",
                    f"git -C {self.root} commit --no-gpg-sign --quiet --message 'Redo {self.sha}'",
                ]
                with subprocess.Popen(
                    "; ".join(commands), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                ) as redo:
                    redo.communicate()
                    if redo.returncode != 0:
                        LOGGER.error(  # pragma: no cover
                            "Redo was unsuccessful. Please consult the logs and git history of your"
                            " database for more information."
                        )
                    else:
                        # update Database
                        Database().read()
                break
        else:
            msg = "Could not find a commit to redo. You must have undone something first!"
            LOGGER.warning(msg)
            sys.exit(1)

        Event.PostRedoCommand.fire(self)
