"""coBib's Search command.

This command allows you to search your database for a regex-interpreted query.
While doing so, it uses the `config.commands.search.grep` tool to search associated files, too.

As a simple example, you can query for a simple author name like so:
```
cobib search Einstein
```
You can make the search case *in*sensitive in two ways:
1. By enabling `config.commands.search.ignore_case`.
2. By providing the `--ignore-case` command-line argument:
```
cobib search --ignore-case Einstein
```

By default, the search command will provide you with 1 line of context above and below the actual
matches. You can change this number of lines by setting the `--context` option:
```
cobib search --context 4 Einstein
```

Finally, you can also combine the search with coBib's filtering mechanism to narrow your search down
to a subset of your database:
```
cobib search Einstein -- ++year 2020
```
Note, that we use the auxiliary `--` argument to separate the filters from the actual arguments.
While this is not strictly necessary it helps to disambiguate the origin of the arguments.

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `/` key.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shlex
import sys
from typing import IO, TYPE_CHECKING, Any, List, Optional, Tuple

from cobib import __version__
from cobib.config import Event, config
from cobib.database import Database

from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class SearchCommand(Command):
    """The Search Command."""

    name = "search"

    def execute(
        self, args: List[str], out: Optional[IO[Any]] = None
    ) -> Optional[Tuple[int, List[str]]]:
        """Searches in the database.

        This command searches the database for a regex-interpreted query.
        It leverages `cobib.database.Entry.search` to perform the actual search.

        You can configure the search-tool which searches through associated files via
        `config.commands.search.grep`.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `query`: the required positional argument corresponds to the regex-interpreted
                      text which will be searched for.
                    * `-i`, `--ignore-case`: if specified, the search will be case *in*sensitive.
                      You can enable this setting permanently with
                      `config.commands.search.ignore_case`.
                    * `-c`, `--context`: you can specify the number of lines of "context" which
                      is the number of lines before and after the actual match to be included in the
                      output. This is similar to `grep`s `-C` option.
                    * in addition to the above, you can add `filters` to narrow the search down to a
                      subset of your database. For more information refer to `cobib.commands.list`.
            out: the output IO stream. This defaults to `None`.

        Returns:
            A tuple containing the number of hits and matching labels.
        """
        LOGGER.debug("Starting Search command.")
        parser = ArgumentParser(prog="search", description="Search subcommand parser.")
        parser.add_argument("query", type=str, help="text to search for")
        parser.add_argument(
            "-i", "--ignore-case", action="store_true", help="ignore case for searching"
        )
        parser.add_argument(
            "-c",
            "--context",
            type=int,
            default=1,
            help="number of context lines to provide for each match",
        )
        parser.add_argument(
            "filter",
            nargs="*",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be modified. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return None

        Event.PreSearchCommand.fire(largs)

        with open(os.devnull, "w", encoding="utf-8") as devnull:
            labels = ListCommand().execute(largs.filter, out=devnull)
        if labels is None:
            return None  # pragma: no cover
        LOGGER.debug("Available entries to search: %s", labels)

        ignore_case = config.commands.search.ignore_case or largs.ignore_case
        re_flags = re.IGNORECASE if ignore_case else 0
        LOGGER.debug("The search will be performed case %ssensitive", "in" if ignore_case else "")

        bib = Database()

        hits = 0
        output = []
        for label in labels.copy():
            entry = bib[label]
            matches = entry.search(largs.query, largs.context, ignore_case)
            if not matches:
                labels.remove(label)
                continue

            hits += len(matches)
            LOGGER.debug('Entry "%s" includes %d hits.', label, hits)
            title = f"{label} - {len(matches)} match" + ("es" if len(matches) > 1 else "")
            title = title.replace(label, config.get_ansi_color("search_label") + label + "\x1b[0m")
            output.append(title)

            for idx, match in enumerate(matches):
                for line in match:
                    line = re.sub(
                        rf"({largs.query})",
                        config.get_ansi_color("search_query") + r"\1" + "\x1b[0m",
                        line,
                        flags=re_flags,
                    )
                    output.append(f"[{idx+1}]\t".expandtabs(8) + line)

        print("\n".join(output), file=out)

        Event.PostSearchCommand.fire(hits, labels)

        return (hits, labels)

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Search command triggered from TUI.")
        tui.viewport.clear()
        # handle input via prompt
        command, results = tui.execute_command("search", out=tui.viewport.buffer)  # type: ignore
        if tui.viewport.buffer.lines and results is not None:
            hits, labels = results
            tui.STATE.mode = "search"
            cur_y, _ = tui.viewport.pad.getyx()
            tui.STATE.previous_line = cur_y
            tui.viewport.buffer.split()
            LOGGER.debug("Applying selection highlighting in search results.")
            for label in labels:
                if label not in tui.selection:
                    continue
                # we match the label including its 'search_label' highlight to ensure that we really
                # only match this specific occurrence of whatever the label may be
                tui.viewport.buffer.replace(
                    range(tui.viewport.buffer.height),
                    re.escape(config.get_ansi_color("search_label")) + label + re.escape("\x1b[0m"),
                    config.get_ansi_color("search_label")
                    + config.get_ansi_color("selection")
                    + label
                    + "\x1b[0m\x1b[0m",
                )
            LOGGER.debug("Populating viewport with search results.")
            tui.viewport.view(ansi_map=tui.ANSI_MAP)
            # reset current cursor position
            LOGGER.debug("Resetting cursor position to top.")
            tui.STATE.top_line = 0
            tui.STATE.current_line = 0
            # update top statusbar
            tui.STATE.topstatus = f"coBib v{__version__} - {hits} hit{'s' if hits > 1 else ''}"
            tui.statusbar(tui.topbar, tui.STATE.topstatus)
            tui.STATE.inactive_commands = ["Add", "Filter", "Sort"]
        elif command[1:]:
            if sys.version_info[1] >= 8:
                joined_command = shlex.join(command[1:])
            else:
                joined_command = shlex.quote(" ".join(command[1:]))
            msg = f"No search hits for '{joined_command}'!"
            LOGGER.info(msg)
            tui.prompt_print(msg)
            tui.viewport.update_list()
