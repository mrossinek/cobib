"""coBib's Redo command.

This command can be used to re-apply the changes *of a previously undone* command:
```
cobib redo
```
This command takes *no* additional arguments!

Note, that if you have not used `cobib undo` previously, this command will have no effect!

Furthermore, this command is *only* available if coBib's git-integration has been enabled and
initialized.
Refer to the documentation of `cobib.commands.init.InitCommand` for more details on that topic.

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `r` key.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import List

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class RedoCommand(Command):
    """The Redo Command."""

    name = "redo"

    def __init__(self, args: List[str]) -> None:
        """TODO."""
        super().__init__(args)

        self.root: Path
        self.sha: str

    @classmethod
    def init_argparser(cls) -> None:
        """TODO."""
        parser = ArgumentParser(prog="redo", description="Redo subcommand parser.")
        cls.argparser = parser

    def execute(self) -> None:
        """Redoes the last undone change.

        This command is *only* available if coBib's git-integration has been enabled via
        `config.database.git` *and* initialized properly (see `cobib.commands.init.InitCommand`).
        If that is the case, this command will re-apply the changes *of a previously undone* command
        (see `cobib.commands.undo.UndoCommand`).

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * **no** additional arguments are required for this subcommand!
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        git_tracked = config.database.git
        if not git_tracked:
            msg = (
                "You must enable coBib's git-tracking in order to use the `Redo` command."
                "\nPlease refer to the man-page for more information on how to do so."
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
