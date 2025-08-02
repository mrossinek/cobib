"""Pass through to the database's git tracking.

.. include:: ../man/cobib-git.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
import subprocess

from typing_extensions import override

from cobib.config import Event, config
from cobib.utils.git import is_inside_work_tree
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class GitCommand(Command):
    """The Git Command.

    This command ignores all arguments passed to it and instead forwards them to the `git`
    executable for further processing.
    """

    name = "git"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="git", description="Git subcommand parser.", exit_on_error=True
        )
        # NOTE: argparse.REMAINDER is undocumented since Python 3.9 and considered a legacy feature.
        # See also https://bugs.python.org/issue17050
        parser.add_argument("git_args", nargs=argparse.REMAINDER, help="the arguments to git")
        cls.argparser = parser

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        largs = super()._parse_args(())
        largs.git_args = args
        return largs

    @override
    def execute(self) -> None:
        git_tracked = config.database.git
        if not git_tracked:
            msg = (
                "You must enable coBib's git-tracking in order to use the `Git` command."
                "\nPlease refer to the documentation for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        file = RelPath(config.database.file).path
        root = file.parent
        if not is_inside_work_tree(root):
            msg = (  # pragma: no cover
                "You have configured, but not initialized coBib's git-tracking."
                "\nPlease consult `cobib init --help` for more information on how to do so."
            )
            LOGGER.error(msg)  # pragma: no cover
            return  # pragma: no cover

        LOGGER.debug("Starting Git command.")

        Event.PreGitCommand.fire(self)

        subprocess.run(["git", "-C", root, *self.largs.git_args], check=False)

        Event.PostGitCommand.fire(self)
