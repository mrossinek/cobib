"""coBib's Show command.

This command simply shows/prints the specified entry as a BibLaTex-formmatted string.
```
cobib show <label>
```

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `ENTER` key.
"""

from __future__ import annotations

import logging
from typing import List

from rich.console import ConsoleRenderable
from rich.syntax import Syntax

from cobib import __version__
from cobib.config import Event
from cobib.database import Database
from cobib.parsers.bibtex import BibtexParser

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class ShowCommand(Command):
    """The Show Command."""

    name = "show"

    def __init__(self, args: List[str]) -> None:
        """TODO."""
        super().__init__(args)

        self.entry_str: str = ""

    @classmethod
    def init_argparser(cls) -> None:
        """TODO."""
        parser = ArgumentParser(prog="show", description="Show subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        cls.argparser = parser

    def execute(self) -> None:
        """Shows an entry in its BibLaTex-format.

        This command simply shows/prints the specified entry as a BibLaTex-formmatted string.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `label`: the label label of the entry to be shown.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Show command.")

        Event.PreShowCommand.fire(self)

        try:
            entry = Database()[self.largs.label]
            entry_str = BibtexParser().dump(entry)

            self.entry_str = entry_str
        except KeyError:
            msg = f"No entry with the label '{self.largs.label}' could be found."
            LOGGER.error(msg)

        Event.PostShowCommand.fire(self)

    def render_rich(self, *, background_color: str = "default") -> ConsoleRenderable:
        """TODO."""
        syntax = Syntax(self.entry_str, "bibtex", background_color=background_color, word_wrap=True)
        return syntax

    def render_porcelain(self) -> List[str]:
        """TODO."""
        return self.entry_str.split("\n")
