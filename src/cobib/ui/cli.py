"""coBib's command-line interface.

This class provides the main entry point to coBib. It exposes all the commands implemented in
`cobib.commands` to the end-user and leverages [`rich`](https://github.com/textualize/rich) to
produce beautiful output.
"""

import argparse
import asyncio
import logging
import sys
from inspect import iscoroutinefunction
from typing import Any

from typing_extensions import override

from cobib import __version__
from cobib.config import config
from cobib.ui.shell import Shell
from cobib.ui.tui import TUI
from cobib.ui.ui import UI
from cobib.utils.console import PromptConsole
from cobib.utils.entry_points import entry_points
from cobib.utils.logging import HINT, print_changelog

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class CLI(UI):
    """The CLI class.

    In addition to the global arguments documented by the base class, the following are supported:

      * `--version`: prints the coBib version and quits.
      * `-s`, `--shell`: starts the interactive `cobib.ui.shell.Shell`.
        This is mutually exclusive with executing a sngle `command` (see below).
      * `command`: a single positional argument indicating the name of the command to run.
        This is mutually exclusive with starting the interactive `--shell` (see above).

    When **neither** the shell **nor** a command are specified, the `cobib.ui.tui.TUI` gets started.
    """

    @override
    def add_extra_parser_arguments(self) -> None:
        command_or_shell = self.parser.add_mutually_exclusive_group()

        command_or_shell.add_argument(
            "-s", "--shell", action="store_true", help="an interactive shell"
        )

        command_or_shell.add_argument(
            "command",
            help="the subcommand to be run",
            choices=sorted([cls.name for (cls, _) in entry_points("cobib.commands")]),
            nargs="?",
        )
        # NOTE: argparse.REMAINDER is undocumented since Python 3.9 and considered a legacy feature.
        # See also https://bugs.python.org/issue17050
        self.parser.add_argument(
            "args", nargs=argparse.REMAINDER, help="any arguments passed on to the subcommand"
        )

        self.parser.add_argument("--version", action="version", version=f"%(prog)s v{__version__}")

    @override
    def parse_args(self) -> argparse.Namespace:
        arguments = super().parse_args()
        # NOTE: we ignore the branching coverage because we test the TUI separately
        if arguments.command is not None:  # pragma: no branch
            sys_args = list(sys.argv)
            subcmd_args = sys_args[sys_args.index(arguments.command) + 1 :]
            if subcmd_args != arguments.args:
                LOGGER.log(  # pragma: no cover
                    HINT,
                    "The arguments provided after the subcommand name did not match the parsed "
                    "ones. This can occur in rare cases when the '--' pseudo-argument is involved. "
                    "Taking an educated guess and overwriting them. Please file a bug report if "
                    "this is a wrong assumption: https://gitlab.com/cobib/cobib/-/issues/new",
                )
                arguments.args = subcmd_args  # pragma: no cover
        return arguments

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.init_argument_parser(
            prog="coBib",
            description=(
                "coBib input arguments.\nIf no subcommand is given, the TUI will be started."
            ),
            epilog=(
                "Read cobib.1, cobib-commands.7, cobib-shell.7 and cobib-tui.7 for more help.\n"
                "To learn more about the configuration, read cobib-config.5.\n"
                "If you are new to coBib, cobib-getting-started.7 is a good starting point."
            ),
        )

    async def run(self) -> None:
        """Runs the CLI interface."""
        arguments = self.parse_args()

        console = PromptConsole.get_instance()

        if not arguments.porcelain:
            # print latest changelog
            changelog = print_changelog(__version__, config.logging.version)
            if changelog is not None:
                # NOTE: we are testing the changelog rendering separately
                console.print(changelog)  # pragma: no cover

        if not arguments.command:
            if arguments.porcelain:
                LOGGER.warning(
                    "The --porcelain mode has no effect on an interactive UI! Ignoring it..."
                )

            InteractiveUI = Shell if arguments.shell else TUI
            task = asyncio.create_task(
                InteractiveUI(verbosity=self.logging_handler.level).run_async()
            )
            await task
            if arguments.logfile:
                arguments.logfile.close()
            # the following is required for the asynchronous TUI to quit properly
            sys.exit()
        else:
            cmd_cls = self.load_command(arguments.command)
            if cmd_cls is None:
                raise RuntimeError(  # pragma: no cover
                    f"Encountered unexpected error: loading the class for '{arguments.command}' "
                    "failed! This should not be possible because the argument parser should catch "
                    "such a case early. When encountering this, please open an issue with steps on "
                    "how to reproduce this problem: https://gitlab.com/cobib/cobib/-/issues/new"
                )

            subcmd = cmd_cls(*arguments.args)
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

        if arguments.logfile:
            arguments.logfile.close()
