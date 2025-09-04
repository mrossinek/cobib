"""coBib's interactive shell.

.. include:: ../man/cobib-shell.7.html_fragment
"""

from __future__ import annotations

import logging
from inspect import iscoroutinefunction
from typing import Any

from rich.live import Live
from typing_extensions import override

from cobib.config import Event
from cobib.ui.components import LoggingHandler, console
from cobib.ui.ui import UI

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ShellLogHandler(LoggingHandler):
    """The Shell's LoggingHandler emit implementation."""

    FORMAT: str = "[%(levelname)s] %(message)s"

    @override
    def emit(self, record: logging.LogRecord) -> None:
        console.log(self.format(record))


class Shell(UI):
    """The Shell class."""

    def __init__(self, *args: Any, verbosity: int = logging.WARNING, **kwargs: Any) -> None:
        """Initializes the TUI.

        Args:
            *args: any positional arguments for textual's underlying `App` class.
            verbosity: the verbosity level of the internal logger.
            **kwargs: any keyword arguments for textual's underlying `App` class.
        """
        super().__init__(*args, **kwargs)

        self.logging_handler = ShellLogHandler(self, level=min(verbosity, logging.WARNING))

        self.history: list[str] = []
        """The history of executed commands and their arguments as a single string (after being
        processed by any PostShellInput event hooks)."""

        self.live: Live
        """The live display in which the console renders."""

    async def run_async(self) -> None:
        """Runs the Shell interface."""
        with Live(console=console, auto_refresh=False) as self.live:
            console.show_cursor(True)

            while True:
                Event.PreShellInput.fire(self)

                text = console.input("> ")

                hook_result = Event.PostShellInput.fire(text)
                if hook_result is not None:
                    text = hook_result

                self.history.append(text)

                command, *args = text.split()

                if command in ("exit", "quit"):
                    break
                elif command == "help":
                    command = "man"
                    args = ["cobib-shell.7"]

                cmd_cls = self.load_command(command)

                if cmd_cls is None:
                    LOGGER.critical(
                        f"Encountered an unknown command: '{command}'! Please try again."
                    )
                    continue

                try:
                    subcmd = cmd_cls(*args)
                    if iscoroutinefunction(subcmd.execute):
                        await subcmd.execute()
                    else:
                        subcmd.execute()

                    renderable = subcmd.render_rich()

                    if renderable is not None:
                        console.print(renderable)

                except SystemExit:
                    pass
