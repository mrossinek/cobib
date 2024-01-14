"""coBib's Show command.

This command simply shows/prints the specified entry as a BibLaTex-formatted string.
```
cobib show <label>
```

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `ENTER` key.
"""

from __future__ import annotations

import logging

from rich.console import Console, ConsoleRenderable
from rich.prompt import PromptBase, PromptType
from rich.syntax import Syntax
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database
from cobib.parsers.bibtex import BibtexParser

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ShowCommand(Command):
    """The Show Command.

    This command can parse the following arguments:

        * `label`: the label of the entry to be shown.
    """

    name = "show"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.entry_str: str = ""
        """The string-formatted `cobib.database.Entry` shown by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="show", description="Show subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        cls.argparser = parser

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Show command.")

        Event.PreShowCommand.fire(self)

        try:
            entry = Database()[self.largs.label]
            entry_str = BibtexParser(encode_latex=config.commands.show.encode_latex).dump(entry)

            self.entry_str = entry_str
        except KeyError:
            msg = f"No entry with the label '{self.largs.label}' could be found."
            LOGGER.error(msg)

        Event.PostShowCommand.fire(self)

    @override
    def render_porcelain(self) -> list[str]:
        return self.entry_str.split("\n")

    @override
    def render_rich(self, *, background_color: str = "default") -> ConsoleRenderable:
        syntax = Syntax(self.entry_str, "bibtex", background_color=background_color, word_wrap=True)
        return syntax
