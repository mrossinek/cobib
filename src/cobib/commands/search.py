"""coBib's Search command.

This command allows you to search your database for one or more regex-interpreted queries.
While doing so, it uses the `cobib.config.config.SearchCommandConfig.grep` tool to search associated
files, too.

As a simple example, you can query for a simple author name like so:
```
cobib search Einstein
```
You can also control whether the search is performed case *in*sensitive.
This is done via the `cobib.config.config.SearchCommandConfig.ignore_case` setting which defaults to
being `False`.
Besides this setting, you can always overwrite its value on the command line with the
`--ignore-case` (`-i` for short) and `--no-ignore-case` (`-I` for short; since v4.1.0) options.
Providing these options takes precedence over your configuration value.
Thus, the following is *always* case *in*sensitive, irrespective of your configuration.
```
cobib search --ignore-case Einstein
```
And the following is *always* sensitive to case:
```
cobib search --no-ignore-case Einstein
```

By default, the search command will provide you with 1 line of context above and below the actual
matches. You can change this number of lines by setting the `--context` option:
```
cobib search --context 4 Einstein
```
You can also permanently change the default value via the
`cobib.config.config.SearchCommandConfig.context` setting.

Finally, you can also combine the search with coBib's filtering mechanism to narrow your search down
to a subset of your database:
```
cobib search Einstein -- ++year 2020
```
Note, that we use the auxiliary `--` argument to separate the filters from the actual arguments.
While this is not strictly necessary it helps to disambiguate the origin of the arguments.

.. note::

   You may also pass other arguments to the `list` command such as `--sort <field>`, `--reverse`, or
   `--limit`. However, these affect which list of entries is being searched over and not the search
   results directly. Thus, the `--limit` will provide an upper bound on the number of entries that
   is being searched and does _not_ indicate the maximum number of search results (since this can
   still be lower).

### Associated files

The search will also be performed on any associated files of your entries.
You can configure the tool which is used to perform this search via the
`cobib.config.config.SearchCommandConfig.grep` setting (defaults to `grep`).

If you do not want to search through associated files, you can specify the `--skip-files` argument.

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `/` key.

.. note::
   For more information on the searching mechanisms see also `cobib.database.Entry.search`.
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from rich.console import Console, ConsoleRenderable
from rich.prompt import PromptBase, PromptType
from rich.text import Text
from rich.tree import Tree
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Entry
from cobib.ui.components import SearchView
from cobib.utils.progress import Progress

from .base_command import ArgumentParser, Command
from .list_ import ListCommand

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class SearchCommand(Command):
    """The Search Command.

    This command can parse the following arguments:

        * `query`: the required positional argument corresponds to the regex-interpreted text which
          will be searched for. You may provide multiple separate queries which will be searched for
          independently.
        * `-i`, `--ignore-case`: if specified, the search will be case-**in**sensitive. This
          overwrites the `cobib.config.config.SearchCommandConfig.ignore_case` setting.
        * `-I`, `--no-ignore-case`: if specified, the search will be case-sensitive. This
          overwrites the `cobib.config.config.SearchCommandConfig.ignore_case` setting.
        * `-c`, `--context`: you can specify the number of lines of "context" which is the number of
          lines before and after the actual match to be included in the output. This is similar to
          the `-C` option of `grep`. You can configure the default value via the
          `cobib.config.config.SearchCommandConfig.context` setting.
        * `--skip-files`: if specified, associated files will **not** be searched.
        * in addition to the above, you can add `filters` to narrow the search down to a subset of
          your database. For more information refer to `cobib.commands.list_`.
    """

    name = "search"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.entries: list[Entry] = []
        """A filtered list of entries searched over by this command."""

        self.matches: list[list[list[str]]] = []
        """The search matches detected by this command. This is a nested list of the following
        structure: the first list level iterates over the entries; the second list level iterates
        over the matches of any given entry; the third list level iterates the (context) lines of
        any given match."""

        self.hits: int = 0
        """The number of search hits detected by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="search", description="Search subcommand parser.")
        parser.add_argument("query", type=str, nargs="+", help="text to search for")
        ignore_case_group = parser.add_mutually_exclusive_group()
        ignore_case_group.add_argument(
            "-i",
            "--ignore-case",
            action="store_true",
            default=None,
            help="ignore case for searching",
        )
        ignore_case_group.add_argument(
            "-I",
            "--no-ignore-case",
            dest="ignore_case",
            action="store_false",
            default=None,
            help="do NOT ignore case for searching",
        )
        parser.add_argument(
            "-c",
            "--context",
            type=int,
            default=config.commands.search.context,
            help="number of context lines to provide for each match",
        )
        parser.add_argument(
            "--skip-files",
            action="store_true",
            default=None,
            help="do NOT search through associated files",
        )
        parser.add_argument(
            "filter",
            nargs="*",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be searched. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )
        cls.argparser = parser

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        search_args = []
        filter_args = []
        found_sep = False
        for arg in args:
            if arg == "--":
                found_sep = True
                continue
            if found_sep:
                filter_args.append(arg)
            else:
                search_args.append(arg)

        largs = super()._parse_args(tuple(search_args))
        largs.filter = filter_args
        return largs

    @override
    async def execute(self) -> None:  # type: ignore[override]
        LOGGER.debug("Starting Search command.")

        Event.PreSearchCommand.fire(self)

        self.entries, _ = ListCommand(*self.largs.filter).execute_dull()

        ignore_case = config.commands.search.ignore_case
        if self.largs.ignore_case is not None:
            ignore_case = self.largs.ignore_case
        LOGGER.debug("The search will be performed case %ssensitive", "in" if ignore_case else "")

        progress_bar = Progress.initialize()
        optional_awaitable = progress_bar.start()  # type: ignore[func-returns-value]
        if optional_awaitable is not None:
            await optional_awaitable

        task = progress_bar.add_task("Searching...", total=len(self.entries))

        for entry in self.entries.copy():
            progress_bar.advance(task, 1)
            await asyncio.sleep(0)

            matches = entry.search(
                self.largs.query, self.largs.context, ignore_case, self.largs.skip_files
            )
            if not matches:
                self.entries.remove(entry)
                continue

            self.matches.append(matches)
            self.hits += len(matches)

            LOGGER.debug('Entry "%s" includes %d hits.', entry.label, len(matches))

        progress_bar.stop()

        Event.PostSearchCommand.fire(self)

    @override
    def render_porcelain(self) -> list[str]:
        output = []
        for entry, matches in zip(self.entries, self.matches):
            title = f"{entry.label}::{len(matches)}"
            output.append(title)

            for idx, match in enumerate(matches):
                for line in match:
                    output.append(f"{idx+1}::" + line.strip())

        return output

    @override
    def render_rich(self) -> ConsoleRenderable:
        ignore_case = config.commands.search.ignore_case
        if self.largs.ignore_case is not None:
            ignore_case = self.largs.ignore_case

        tree = Tree(".", hide_root=True)
        for entry, matches in zip(self.entries, self.matches):
            subtree = tree.add(
                Text.from_markup(
                    f"[search.label]{entry.markup_label()}[/search.label] - {len(matches)} match"
                    + ("es" if len(matches) > 1 else "")
                )
            )

            for idx, match in enumerate(matches):
                matchtree = subtree.add(str(idx + 1))
                for line in match:
                    line_text = Text(line)
                    line_text.highlight_words(
                        self.largs.query,
                        config.theme.search.query,
                        case_sensitive=not ignore_case,
                    )
                    matchtree.add(line_text)

        return tree

    @override
    def render_textual(self) -> SearchView:
        ignore_case = config.commands.search.ignore_case
        if self.largs.ignore_case is not None:
            ignore_case = self.largs.ignore_case

        tree = SearchView(".")
        for entry, matches in zip(self.entries, self.matches):
            data = entry.label
            subtree = tree.root.add(
                Text.from_markup(
                    f"[search.label]{entry.markup_label()}[/search.label] - {len(matches)} match"
                    + ("es" if len(matches) > 1 else "")
                ),
                data=data,
                expand=not config.tui.tree_folding[0],
            )

            for idx, match in enumerate(matches):
                matchtree = subtree.add(
                    str(idx + 1),
                    data=data,
                    expand=not config.tui.tree_folding[1],
                )
                for line in match:
                    line_text = Text(line)
                    line_text.highlight_words(
                        self.largs.query,
                        config.theme.search.query,
                        case_sensitive=not ignore_case,
                    )
                    matchtree.add_leaf(line_text, data=data)

        return tree
