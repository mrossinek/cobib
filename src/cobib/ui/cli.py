"""TODO."""

import argparse
import asyncio
import logging
import sys
from inspect import iscoroutinefunction
from typing import Any

from rich.console import Console

from cobib import __version__, commands
from cobib.config import config
from cobib.database import Database
from cobib.ui.tui import TUI
from cobib.ui.ui import UI
from cobib.utils import shell_helper
from cobib.utils.logging import print_changelog

LOGGER = logging.getLogger(__name__)


class CLI(UI):
    """TODO."""

    def add_extra_parser_arguments(self) -> None:
        """TODO."""
        self.parser.add_argument("--version", action="version", version=f"%(prog)s v{__version__}")

        subcommands = [cmd.split(":")[0] for cmd in shell_helper.list_commands([])]
        self.parser.add_argument(
            "command", help="subcommand to be called", choices=subcommands, nargs="?"
        )
        self.parser.add_argument("args", nargs=argparse.REMAINDER)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """TODO."""
        super().__init__(*args, **kwargs)

        self.init_argument_parser(
            prog="coBib",
            description=(
                "Cobib input arguments.\nIf no arguments are given, the TUI will start as a "
                "default."
            ),
        )

    async def run(self) -> None:
        """TODO."""
        arguments = self.parse_args()

        console = Console()

        if not arguments.porcelain:
            # print latest changelog
            changelog = print_changelog(__version__, config.logging.version)
            if changelog is not None:
                console.print(changelog)

        if arguments.command == "init":
            # the database file may not exist yet, thus we ensure to execute the command before
            # trying to read the database file
            subcmd = getattr(commands, "InitCommand")(arguments.args)
            subcmd.execute()
            return

        # initialize database
        Database()

        if not arguments.command:
            task = asyncio.create_task(TUI().run_async())
            await task
            sys.exit()
        else:
            subcmd = getattr(commands, arguments.command.title() + "Command")(arguments.args)
            if iscoroutinefunction(subcmd.execute):
                await subcmd.execute()
            else:
                subcmd.execute()
            if arguments.porcelain:
                output = subcmd.render_porcelain()
                for line in output:
                    print(line)
            else:
                renderable = subcmd.render_rich()
                if renderable is not None:
                    console.print(renderable)
