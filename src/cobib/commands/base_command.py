"""coBib's Command interface."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import sys
from abc import ABC, abstractmethod

from rich.console import Console, ConsoleRenderable
from rich.prompt import Prompt, PromptBase, PromptType
from textual.app import App
from textual.widget import Widget

from cobib.config import Event, config
from cobib.ui.components import ArgumentParser as ArgumentParser  # noqa: PLC0414
from cobib.utils.rel_path import RelPath

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class Command(ABC):
    """The Command interface.

    This interface should be implemented by all concrete command implementations.
    """

    name = "base"
    """The commands `name` is used to extract the available commands for the command-line interface.
    """

    argparser: ArgumentParser
    """Every command has its own `argparse.ArgumentParser` which is used to parse the arguments
    provided to the command. This is done no matter how the command is executed, whether
    programmatically via Python, from the command-line or any other UI."""

    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        """Initializes a command instance.

        Args:
            *args: the sequence of additional command arguments. These will be passed on to the
                `argparser` of this command for further parsing.
            console: a command may be in need of printing something for the user during its
                execution (and before its final result rendering). If so, it should use the `print`
                method of this console object.
            prompt: a command may be in need of prompting the user for an input. If so, it will use
                this prompt kind. It is important that this is respected, as different UIs may
                inject specific prompt classes to implement different runtime behavior.
        """
        self.args: tuple[str, ...] = args
        """The raw provided command arguments."""

        self.largs: argparse.Namespace = self.__class__._parse_args(args)
        """The parsed (local) arguments."""

        if console is not None:
            LOGGER.log(
                45,
                "The `console` argument to all the commands is DEPRECATED since it no longer has "
                "any effect.",
            )
        self.console: Console | App[None] = console if console is not None else Console()
        """DEPRECATED The object via which to print output to the user during runtime execution."""

        if prompt is not None:
            LOGGER.log(
                45,
                "The `prompt` argument to all the commands is DEPRECATED since it no longer has "
                "any effect.",
            )
        self.prompt: type[PromptBase[PromptType]] = prompt if prompt is not None else Prompt
        """DEPRECATED The object via which to prompt the user for input during runtime execution."""

    @classmethod
    @abstractmethod
    def init_argparser(cls) -> None:
        """Initializes this command's `argparse.ArgumentParser`.

        This method needs to be overwritten by every subclass and handles the registration of all
        available command arguments.
        """

    @classmethod
    def _get_argparser(cls) -> ArgumentParser:
        """Returns this command's `argparse.ArgumentParser`.

        The reason for having this method is to handle the parser initialization such that it only
        needs to be done once.

        Returns:
            This command's initialized `argparser` object.
        """
        if hasattr(cls, "argparser"):
            return cls.argparser

        cls.init_argparser()
        return cls.argparser

    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        """Parses the provided command arguments.

        Args:
            args: the sequence of additional command arguments provided to the command upon
                initialization.

        Returns:
            The parsed arguments namespace.
        """
        try:
            largs = cls._get_argparser().parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            sys.exit(1)

        return largs

    @abstractmethod
    def execute(self) -> None:
        """Actually executes the command.

        This means, all of the command-specific logic and action needs to be implemented by this
        method.

        .. note::
           This method is **not** in charge of presenting the final result to the user. Refer to the
           various `render_*` methods, instead.

        As a consequence, resulting data should be stored on the command instance (which also has
        the benefit of exposing this data to the various `Post*Command` `cobib.config.event.Event`
        hooks.

        This function may *not* raise any errors!
        This also means it should take care of catching all potential errors triggered by internally
        used methods.
        Such encountered errors should be logged and the method should return gracefully.
        """

    def render_porcelain(self) -> list[str]:
        """Renders the command results in "porcelain" mode.

        This method is called when the `--porcelain` argument has been provided.
        The idea is to provide an output mode which is easily parse-able by another program or
        function.

        Returns:
            A list of strings where each entry should be considered one line of output.
        """
        return []

    def render_rich(self) -> ConsoleRenderable | None:
        """Renders the command results as a `rich` object.

        This method is called when a command is run via the command-line interface.

        Returns:
            An optional `ConsoleRenderable` to be presented to the user.
        """
        return None

    def render_textual(self) -> Widget | None:
        """Renders the command results as a `textual` widget.

        This method is called when a command is run via the terminal user interface.
        It is the responsibility of the TUI to deal with the returned widget.

        Returns:
            An optional `Widget` to be rendered in the TUI.
        """
        return None

    def git(self, force: bool = False, *, allow_empty: bool = False) -> None:
        """Generates a git commit to track the commands changes.

        This function only has an effect when `cobib.config.config.DatabaseConfig.git` is enabled
        *and* the database has been initialized correctly with `cobib.commands.init`.
        Otherwise, a warning will be printed and no commit will be generated.
        Nonetheless, the changes applied by the commit will have taken effect in the database.

        This method uses the parsed arguments (`largs`) to include command execution information in
        the generated commit message.

        Args:
            force: whether to ignore the configuration setting. This option is mainly used by the
                `cobib.commands.init.InitCommand`.
            allow_empty: whether to allow an empty commit to be created. Normally, this is a
                mistake, but some commands may want to enforce a commit.
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

        git_commit_args = ["--no-gpg-sign", "--quiet"]
        if allow_empty:
            git_commit_args.append("--allow-empty")
        commands = [
            f"cd {root}",
            f"git add -- {file}",
            f"git commit {' '.join(git_commit_args)} --message {shlex.quote(msg)}",
        ]
        LOGGER.debug("Auto-commit to git from %s command.", self.name)
        os.system("; ".join(commands))

        Event.PostGitCommit.fire(root, file)
