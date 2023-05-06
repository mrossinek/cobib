"""coBib's Command interface."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import sys
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from rich.console import Console, ConsoleRenderable
from rich.prompt import PromptBase
from textual.app import App

from cobib.config import Event, config
from cobib.ui.argument_parser import ArgumentParser as ArgumentParser
from cobib.utils.rel_path import RelPath

LOGGER = logging.getLogger(__name__)


class Command(ABC):
    """The Command interface.

    This interface should be implemented by all concrete command implementations.
    """

    name = "base"
    """The commands `name` is used to extract the available commands for the command-line interface.
    """

    argparser: ArgumentParser
    """TODO."""

    prompt: Type[PromptBase[str]] | None = None
    """TODO."""

    console: Console | App[None] | None = None
    """TODO."""

    def __init__(self, args: List[str]) -> None:
        """The initializer of any concrete implementation should *not* take any arguments!"""
        self.args = args
        self.largs = self.__class__._parse_args(args)

    @abstractmethod
    def execute(self) -> None:
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
            for ease of additional post-processing.
        """

    @classmethod
    def get_argparser(cls) -> ArgumentParser:
        """TODO."""
        if hasattr(cls, "argparser"):
            return cls.argparser

        cls.init_argparser()
        return cls.argparser

    @classmethod
    @abstractmethod
    def init_argparser(cls) -> None:
        """TODO."""

    @classmethod
    def _parse_args(cls, args: List[str]) -> argparse.Namespace:
        """TODO."""
        try:
            largs = cls.get_argparser().parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            sys.exit(1)

        return largs

    def render_rich(self) -> Optional[ConsoleRenderable]:
        """TODO."""
        return None

    def render_porcelain(self) -> List[str]:
        """TODO."""
        return []

    def git(self, force: bool = False) -> None:
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

        args = vars(self.largs)
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
