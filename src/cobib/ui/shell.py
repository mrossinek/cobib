"""coBib's interactive shell.

.. include:: ../man/cobib-shell.7.html_fragment
"""

from __future__ import annotations

import logging
from inspect import iscoroutinefunction
from typing import Any

from rich.console import ConsoleRenderable, RenderHook
from rich.control import Control
from rich.live import Live

from cobib.config import Event
from cobib.ui.ui import UI
from cobib.utils.console import PromptConsole

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class Shell(UI, RenderHook):
    """The Shell class."""

    def __init__(self, *args: Any, verbosity: int = logging.WARNING, **kwargs: Any) -> None:
        """Initializes the TUI.

        Args:
            *args: any positional arguments for textual's underlying `App` class.
            verbosity: the verbosity level of the internal logger.
            **kwargs: any keyword arguments for textual's underlying `App` class.
        """
        super().__init__(*args, **kwargs)
        self.logging_handler.setLevel(min(verbosity, logging.WARNING))

        self.console: PromptConsole = PromptConsole.get_instance()
        """The console instance."""

        self.live: Live
        """The live display in which the console renders."""

    async def run_async(self) -> None:
        """Runs the Shell interface."""
        with Live(console=self.console, auto_refresh=False) as self.live:
            self.console.show_cursor(True)

            self.console.push_render_hook(self)

            while True:
                Event.PreShellInput.fire(self)

                text = await self.console.input("> ")

                hook_result = Event.PostShellInput.fire(text)
                if hook_result is not None:
                    text = hook_result

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
                        self.console.print(renderable)

                except SystemExit:
                    pass

    def process_renderables(self, renderables: list[ConsoleRenderable]) -> list[ConsoleRenderable]:
        """Process renderables to remove any cursor positioning Control.

        This is necessary because we delegate this task to `prompt_toolkit`.

        Args:
            renderables: the renderable object to process.

        Returns:
            The processed renderable objects.
        """
        if isinstance(renderables[0], Control):
            renderables = renderables[1:]
        return renderables
