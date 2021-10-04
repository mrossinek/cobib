"""coBib's Show command.

This command simply shows/prints the specified entry as a BibLaTex-formmatted string.
```
cobib show <label>
```

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `ENTER` key.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import IO, TYPE_CHECKING, Any, List

from cobib import __version__
from cobib.config import Event, config
from cobib.database import Database
from cobib.parsers.bibtex import BibtexParser

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class ShowCommand(Command):
    """The Show Command."""

    name = "show"

    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Shows an entry in its BibLaTex-format.

        This command simply shows/prints the specified entry as a BibLaTex-formmatted string.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `label`: the label label of the entry to be shown.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Show command.")
        parser = ArgumentParser(prog="show", description="Show subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return

        Event.PreShowCommand.fire(largs)

        try:
            entry = Database()[largs.label]
            entry_str = BibtexParser().dump(entry)

            entry_str = Event.PostShowCommand.fire(entry_str) or entry_str

            print(entry_str, file=out)
        except KeyError:
            msg = f"No entry with the label '{largs.label}' could be found."
            LOGGER.error(msg)

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Show command triggered from TUI.")
        # get current label
        label, cur_y = tui.viewport.get_current_label()
        # populate buffer with entry data
        LOGGER.debug("Clearing current buffer contents.")
        tui.viewport.clear()
        ShowCommand().execute([label], out=tui.viewport.buffer)  # type: ignore
        tui.viewport.buffer.split()
        if label in tui.selection:
            LOGGER.debug("Current entry is selected. Applying highlighting.")
            tui.viewport.buffer.replace(
                0, label, config.get_ansi_color("selection") + label + "\x1b[0m"
            )
        LOGGER.debug("Populating buffer with ShowCommand result.")
        tui.viewport.view(ansi_map=tui.ANSI_MAP)

        # reset current cursor position
        tui.STATE.top_line = 0
        tui.STATE.current_line = 0
        # update top statusbar
        tui.STATE.topstatus = f"coBib v{__version__} - {label}"
        tui.statusbar(tui.topbar, tui.STATE.topstatus)
        # enter show menu
        tui.STATE.mode = "show"
        tui.STATE.previous_line = cur_y
        tui.STATE.inactive_commands = ["Add", "Filter", "Show", "Sort"]
