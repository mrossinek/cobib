"""coBib's Command interface."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import sys
from abc import ABC, abstractmethod
from typing import IO, TYPE_CHECKING, Any, Dict, Generator, List, NoReturn, Optional

from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class Command(ABC):
    """The Command interface.

    This interface should be implemented by all concrete command implementations.
    In order to provide both, command-line and TUI usability, the `execute` and `tui` functions must
    be implemented, respectively.
    """

    name = "base"
    """The commands `name` is used to extract the available commands for the command-line interface.
    """

    def __init__(self) -> None:
        """The initializer of any concrete implementation should *not* take any arguments!"""

    @abstractmethod
    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> Any:
        """Actually executes the command.

        This means, all of the command-specific logic and action needs to be implemented by this
        method.
        It also poses as the pure interface triggered from the command-line.
        The arguments given to this function are parsed by `argparse` which also means that each
        subcommand should provide an additional `--help` menu for the command-line interface.
        ```
        cobib <subcommand> --help
        ```

        This function may *not* raise any errors!
        This also means it should take care of catching all potential errors triggered by internally
        used methods.
        Such encountered errors should be logged and the method should return gracefully.

        Args:
            args: a sequence of additional arguments used for the execution.
            out: the output IO stream. This defaults to `sys.stdout`.

        Returns:
            Usually `None` but some complex commands may choose to return some of their runtime data
            for ease of additional post-processing in (e.g.) the `tui` wrapper.
        """

    @staticmethod
    @abstractmethod
    def tui(tui: cobib.tui.TUI) -> Optional[Generator[List[str], None, None]]:
        """TUI command interface.

        This function serves as the commands entry-point from the `cobib.tui.tui.TUI` instance.
        It should take care of any pre- and/or post-processing before calling `execute` internally
        to do the actual work.

        The processing may involve handling of highlighting as well as general screen buffer
        contents.

        Args:
            tui: the runtime-instance of coBib's TUI.

        Yields:
            Optionally, this method may `yield` the command arguments for further processing.
        """

    def git(self, args: Optional[Dict[str, Any]] = None, force: bool = False) -> None:
        """Generates a git commit to track the commands changes.

        This function only has an effect when `config.database.git` is enabled *and* the database
        has been initialized correctly with `cobib.commands.init.InitCommand`.
        Otherwise, a warning will be printed and no commit will be generated.
        Nonetheless, the changes applied by the commit will have taken effect in the database.

        Args:
            args: a dictionary containing the *parsed* command arguments.
            force: whether to ignore the configuration setting. This option is mainly used by the
                `cobib.commands.init.InitCommand`.
        """
        git_tracked = config.database.git
        if not git_tracked and not force:
            return

        file = RelPath(config.database.file).path
        root = file.parent

        if not (root / ".git").exists():
            if git_tracked:
                msg = (
                    "You have configured coBib to track your database with git."
                    "\nPlease run `cobib init --git`, to initialize this tracking."
                )
                LOGGER.warning(msg)
                return

        msg = f"Auto-commit: {self.name.title()}Command"
        if args:
            msg += "\n\n"
            msg += json.dumps(args, indent=2, default=str)

        msg = Event.PreGitCommit.fire(msg, args) or msg

        commands = [
            f"cd {root}",
            f"git add -- {file}",
            f"git commit --no-gpg-sign --quiet --message {shlex.quote(msg)}",
        ]
        LOGGER.debug("Auto-commit to git from %s command.", self.name)
        os.system("; ".join(commands))

        Event.PostGitCommit.fire(root, file)


class ArgumentParser(argparse.ArgumentParser):
    """Wrapper of the `argparse.ArgumentParser` to allow catching of error messages.

    Note, this class will be removed once Python 3.9 becomes the minimal supported version as it
    added the [`exit_on_error`](https://docs.python.org/3/library/argparse.html#exit-on-error)
    keyword argument.
    """

    # TODO: once Python 3.9 becomes the default, make use of the exit_on_error argument.

    def exit(self, status: int = 0, message: Optional[str] = None) -> NoReturn:
        """Overwrite the exit method to raise an error rather than exit.

        Args:
            status: the status code. If non-zero, an `argparse.ArgumentError` will be raised.
            message: the message of the error.

        Raises:
            An `argparse.ArgumentError`.
        """
        if status:
            raise argparse.ArgumentError(None, f"Error: {message}")
        super().exit(status, message)  # pragma: no cover
