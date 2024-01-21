"""coBib's command-line interface.

This class provides the main entry point to coBib. It exposes all the commands implemented in
`cobib.commands` to the end-user and leverages [`rich`](https://github.com/textualize/rich) to
produce beautiful output.
"""

import argparse
import asyncio
import inspect
import logging
import sys
from inspect import iscoroutinefunction
from typing import Any

from rich.console import Console
from typing_extensions import override

from cobib import __version__, commands
from cobib.config import config
from cobib.database import Database
from cobib.ui.tui import TUI
from cobib.ui.ui import UI
from cobib.utils.logging import print_changelog

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class CLI(UI):
    """The CLI class.

    In addition to the global arguments documented by the base class, the following are supported:

      * `--version`: prints the coBib version and quits.
      * `command`: a single positional argument indicating the name of the command to run. When this
        is omitted, the `cobib.ui.tui.TUI` gets started.
    """

    @override
    def add_extra_parser_arguments(self) -> None:
        self.parser.add_argument("--version", action="version", version=f"%(prog)s v{__version__}")

        subcommands = [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]
        self.parser.add_argument(
            "command", help="subcommand to be called", choices=subcommands, nargs="?"
        )
        self.parser.add_argument("args", nargs=argparse.REMAINDER)

    @override
    def parse_args(self) -> argparse.Namespace:
        arguments = super().parse_args()
        if arguments.command is not None:
            sys_args = list(sys.argv)
            subcmd_args = sys_args[sys_args.index(arguments.command) + 1 :]
            if subcmd_args != arguments.args:
                LOGGER.log(
                    35,
                    "The arguments provided after the subcommand name did did not match the parsed "
                    "ones. This can occur in rare cases when the '--' pseudo-argument is involved. "
                    "Taking an educated guess and overwriting them. Please file a bug report if "
                    "this is a wrong assumption: https://gitlab.com/cobib/cobib/-/issues/new",
                )
                arguments.args = subcmd_args
        return arguments

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.init_argument_parser(
            prog="coBib",
            description=(
                "Cobib input arguments.\nIf no arguments are given, the TUI will start as a "
                "default."
            ),
        )

    @override
    async def run(self) -> None:  # type: ignore[override]
        arguments = self.parse_args()

        console = Console(theme=config.theme.build())

        if not arguments.porcelain:
            # print latest changelog
            changelog = print_changelog(__version__, config.logging.version)
            if changelog is not None:
                console.print(changelog)

        if arguments.command == "init":
            # the database file may not exist yet, thus we ensure to execute the command before
            # trying to read the database file
            subcmd = getattr(commands, "InitCommand")(*arguments.args)
            subcmd.execute()
            return

        # initialize database
        Database()

        if not arguments.command:
            task = asyncio.create_task(TUI().run_async())  # type: ignore[abstract]
            await task
            # the following is required for the asynchronous TUI to quit properly
            sys.exit()
        else:
            subcmd = getattr(commands, arguments.command.title() + "Command")(*arguments.args)
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
