"""coBib's Open command.

This command can be used to open associated files of an entry.
```
cobib open <label 1> [<label 2> ...]
```

The `file` and `url` fields of `cobib.database.Entry.data` are queried for Path or URL strings.
If one such string is found, it is automatically opened with the program configured by
`config.commands.open.command`.
If multiple matches are found, the user will be presented with a menu to choose one or multiple
matches.

This menu will look similar to the following after querying for `help`:
```
You can specify one of the following options:
  1. a url number
  2. a field name provided in '[...]'
  3. or simply 'all'
  4. ENTER will abort the command

  1: [file] /path/to/a/file.pdf
  2: [file] /path/to/another/file.pdf
  3: [url] https://example.org/
Entry to open [Type 'help' for more info]:
```

With the above options, here is what will happen depending on the users choice:
* `1`, `2`, or `3`: will open the respective file or URL.
* `file` or `url`: will open the respective group.
* `all`: will open all matches.
* `help`: will print the detailed help-menu again.
* `ENTER`: will abort the command.

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `o` key.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from collections import defaultdict
from typing import IO, TYPE_CHECKING, Any, Dict, List
from urllib.parse import ParseResult, urlparse

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class OpenCommand(Command):
    """The Open Command."""

    name = "open"

    # pylint: disable=too-many-branches
    def execute(self, args: List[str], out: IO[Any] = sys.stderr) -> None:
        """Opens associated files of an entry.

        This command opens the associated file(s) of one (or multiple) entries.
        It does so by querying the `file` and `url` fields of `cobib.database.Entry.data`.
        If multiple such files are found, the user is presented with a menu allowing him to choose
        one or multiple files to be opened.

        The command for opening can be configured via `config.commands.open.command`.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `labels`: one (or multiple) labels of the entries to be opened.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Open command.")
        parser = ArgumentParser(prog="open", description="Open subcommand parser.")
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return

        Event.PreOpenCommand.fire(largs)

        bib = Database()

        # pylint: disable=too-many-nested-blocks
        for label in largs.labels:
            things_to_open: Dict[str, List[ParseResult]] = defaultdict(list)
            count = 0
            # first: find all possible things to open
            try:
                entry = bib[label]
                for field in ("file", "url"):
                    if field in entry.data.keys() and entry.data[field]:
                        value = entry.data[field]
                        for val in value:
                            val = val.strip()
                            LOGGER.debug('Parsing "%s" for URLs.', val)
                            things_to_open[field] += [urlparse(val)]
                            count += 1
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                LOGGER.warning(msg)
                continue

            # if there are none, skip current label
            if not things_to_open:
                msg = f"The entry '{label}' has no actionable field associated with it."
                LOGGER.warning(msg)
                continue

            if count == 1:
                # we found a single URL to open
                self._open_url(list(things_to_open.values())[0][0])
            else:
                # we query the user what to do
                idx = 1
                url_list = []
                prompt: List[str] = []
                # print formatted list of available URLs
                for field, urls in things_to_open.items():
                    for url in urls:
                        prompt.append(f"{idx:3}: [{field}] {url.geturl()}")
                        url_list.append(url)
                        idx += 1
                # loop until the user picks a valid choice
                help_requested = False
                while True:
                    prompt_copy = prompt.copy()
                    prompt_copy.append("Entry to open [Type 'help' for more info]: ")
                    try:
                        choice = input("\n".join(prompt_copy)).strip()
                    except EOFError:
                        choice = ""
                    if not choice:
                        # empty input
                        msg = "User aborted open command."
                        LOGGER.warning(msg)
                        break
                    if choice == "help":
                        LOGGER.debug("User requested help.")
                        if not help_requested:
                            prompt = [
                                "You can specify one of the following options:",
                                "  1. a url number",
                                "  2. a field name provided in '[...]'",
                                "  3. or simply 'all'",
                                "  4. ENTER will abort the command",
                                "",
                            ] + prompt
                        help_requested = True
                    elif choice == "all":
                        LOGGER.debug("User selected all urls.")
                        for url in url_list:
                            self._open_url(url)
                        break
                    elif choice in things_to_open.keys():
                        LOGGER.debug("User selected the %s set of urls.", choice)
                        for url in things_to_open[choice]:
                            self._open_url(url)
                        break
                    elif choice.isdigit() and int(choice) > 0 and int(choice) <= count:
                        LOGGER.debug("User selected url %s", choice)
                        self._open_url(url_list[int(choice) - 1])
                        break

        Event.PostOpenCommand.fire(largs.labels)

    @staticmethod
    def _open_url(url: ParseResult) -> None:
        """Opens a URL."""
        opener = config.commands.open.command
        try:
            url_str: str = url.geturl() if url.scheme else str(RelPath(url.geturl()).path)
            LOGGER.debug('Opening "%s" with %s.', url_str, opener)
            with open(os.devnull, "w", encoding="utf-8") as devnull:
                subprocess.Popen(  # pylint: disable=consider-using-with
                    [opener, url_str], stdout=devnull, stderr=devnull, stdin=devnull, close_fds=True
                )
        except FileNotFoundError as err:
            LOGGER.error(err)

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Open command triggered from TUI.")
        if tui.selection:
            # use selection for command
            labels = list(tui.selection)
        else:
            # get current label
            label, _ = tui.viewport.get_current_label()
            labels = [label]
        tui.execute_command(["open"] + labels, skip_prompt=True)
