"""coBib's Undo command.

This command can be used to undo the changes of the a previous command.
```
cobib undo
```
For obvious reasons, this will only undo commands which had an effect on the contents of the
database file.
Moreover, as a safety measure, this command will only undo those changes, which have been committed
by coBib *automatically*.
You can disable this be setting the `--force` argument which *always* undoes the last commit.

Furthermore, this command is *only* available if coBib's git-integration has been enabled and
initialized.
Refer to the documentation of `cobib.commands.init.InitCommand` for more details on that topic.

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `u` key.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from typing import IO, TYPE_CHECKING, Any, List

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class UndoCommand(Command):
    """The Undo Command."""

    name = "undo"

    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Undoes the last change.

        This command is *only* available if coBib's git-integration has been enabled via
        `config.database.git` *and* initialized properly (see `cobib.commands.init.InitCommand`).
        If that is the case, this command will undo the changes of a previous command.
        Note, that this *only* applies to commands whose changes have been committed by coBib
        *automatically*.
        This is a safety measure which you can disable by setting the `--force` argument.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `-f`, `--force`: if specified, this will also revert changes which have *not*
                      been auto-committed by coBib.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        git_tracked = config.database.git
        if not git_tracked:
            msg = (
                "You must enable coBib's git-tracking in order to use the `Undo` command."
                "\nPlease refer to the man-page for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        file = RelPath(config.database.file).path
        root = file.parent
        if not (root / ".git").exists():
            msg = (
                "You have configured, but not initialized coBib's git-tracking."
                "\nPlease consult `cobib init --help` for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        LOGGER.debug("Starting Undo command.")
        parser = ArgumentParser(prog="undo", description="Undo subcommand parser.")
        parser.add_argument(
            "-f", "--force", action="store_true", help="allow undoing non auto-committed changes"
        )

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return

        Event.PreUndoCommand.fire(largs)

        LOGGER.debug("Obtaining git log.")
        lines = subprocess.check_output(
            [
                "git",
                "--no-pager",
                "-C",
                f"{root}",
                "log",
                "--oneline",
                "--no-decorate",
                "--no-abbrev",
            ]
        )
        undone_shas = set()
        for commit in lines.decode().strip().split("\n"):
            LOGGER.debug("Processing commit %s", commit)
            sha, *message = commit.split()
            if message[0] == "Undo":
                # Store already undone commit sha
                LOGGER.debug("Storing undone commit sha: %s", message[-1])
                undone_shas.add(message[-1])
                continue
            if sha in undone_shas:
                LOGGER.info("Skipping %s as it was already undone", sha)
                continue
            if largs.force or (message[0] == "Auto-commit:" and message[-1] != "InitCommand"):
                # we undo a commit if and only if:
                #  - the `force` argument is specified OR
                #  - the commit is an `auto-committed` change which is NOT from `InitCommand`
                LOGGER.debug("Attempting to undo %s.", sha)
                commands = [
                    f"git -C {root} revert --no-commit {sha}",
                    f"git -C {root} commit --no-gpg-sign --quiet --message 'Undo {sha}'",
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

        Event.PostUndoCommand.fire(root, sha)

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Undo command triggered from TUI.")
        tui.execute_command(["undo"], skip_prompt=True)
        # update database list
        LOGGER.debug("Updating list after Undo command.")
        tui.viewport.update_list()
