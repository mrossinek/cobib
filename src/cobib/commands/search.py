"""Search in the database.

.. include:: ../man/cobib-search.1.html_fragment
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from rich.console import ConsoleRenderable
from rich.text import Text
from rich.tree import Tree
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Entry
from cobib.ui.components import SearchView
from cobib.utils.match import Match
from cobib.utils.progress import Progress
from cobib.utils.regex import HAS_OPTIONAL_REGEX

from .base_command import Command
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
        * `-l`, `--decode-latex`: if specified, all LaTeX sequences will be decoded before searched.
          This overwrites the `cobib.config.config.SearchCommandConfig.decode_latex` setting.
        * `-L`, `--no-decode-latex`: if specified, LaTeX sequences will be left unchanged before
          searched. This overwrites the `cobib.config.config.SearchCommandConfig.decode_latex`
          setting.
        * `-u`, `--decode-unicode`: if specified, all Unicode characters will be decoded before
          searched. This overwrites the `cobib.config.config.SearchCommandConfig.decode_unicode`
          setting.
        * `-U`, `--no-decode-unicode`: if specified, Unicode characters will be left unchanged
          before searched. This overwrites the
          `cobib.config.config.SearchCommandConfig.decode_unicode` setting.
        * `-z`, `--fuzziness`: you can specify the number of fuzzy errors to allow for search
          matches. This requires the optional `regex` dependency to be installed.
        * `-c`, `--context`: you can specify the number of lines of "context" which is the number of
          lines before and after the actual match to be included in the output. This is similar to
          the `-C` option of `grep`. You can configure the default value via the
          `cobib.config.config.SearchCommandConfig.context` setting.
        * `--skip-files`: if specified, associated files will **not** be searched. This overwrites
            the `cobib.config.config.SearchCommandConfig.skip_files` setting.
        * `--include-files`: if specified, associated files will be searched. This overwrites
            the `cobib.config.config.SearchCommandConfig.skip_files` setting.
        * `--skip-notes`: if specified, associated notes will **not** be searched. This overwrites
            the `cobib.config.config.SearchCommandConfig.skip_notes` setting.
        * `--include-notes`: if specified, associated notes will be searched. This overwrites
            the `cobib.config.config.SearchCommandConfig.skip_notes` setting.
        * in addition to the above, you can add `filters` to narrow the search down to a subset of
          your database. For more information refer to `cobib.commands.list_`.
    """

    name = "search"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.entries: list[Entry] = []
        """A filtered list of entries searched over by this command."""

        self.matches: list[list[Match]] = []
        """The search matches detected by this command. This is a nested list of the following
        structure: the first list level iterates over the entries; the second list level iterates
        over the matches of any given entry; the third list level iterates the (context) lines of
        any given match."""

        self.hits: int = 0
        """The number of search hits detected by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="search",
            description="Search subcommand parser.",
            epilog="Read cobib-search.1 for more help.",
        )
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
        latex_group = parser.add_mutually_exclusive_group()
        latex_group.add_argument(
            "-l",
            "--decode-latex",
            action="store_true",
            default=None,
            help="decode LaTeX sequences for searching",
        )
        latex_group.add_argument(
            "-L",
            "--no-decode-latex",
            dest="decode_latex",
            action="store_false",
            default=None,
            help="do NOT decode LaTeX sequences for searching",
        )
        unicode_group = parser.add_mutually_exclusive_group()
        unicode_group.add_argument(
            "-u",
            "--decode-unicode",
            action="store_true",
            default=None,
            help="decode Unicode characters for searching",
        )
        unicode_group.add_argument(
            "-U",
            "--no-decode-unicode",
            dest="decode_unicode",
            action="store_false",
            default=None,
            help="do NOT decode Unicode characters for searching",
        )
        parser.add_argument(
            "-z",
            "--fuzziness",
            type=int,
            default=config.commands.search.fuzziness,
            help=(
                "how many fuzzy errors to allow for search matches. This requires the optional "
                "`regex` dependency to be installed."
            ),
        )
        parser.add_argument(
            "-c",
            "--context",
            type=int,
            default=config.commands.search.context,
            help="number of context lines to provide for each match",
        )
        files_group = parser.add_mutually_exclusive_group()
        files_group.add_argument(
            "--skip-files",
            action="store_true",
            default=None,
            help="do NOT search through associated files",
        )
        files_group.add_argument(
            "--include-files",
            dest="skip_files",
            action="store_false",
            default=None,
            help="DO search through associated files",
        )
        notes_group = parser.add_mutually_exclusive_group()
        notes_group.add_argument(
            "--skip-notes",
            action="store_true",
            default=None,
            help="do NOT search through associated notes",
        )
        notes_group.add_argument(
            "--include-notes",
            dest="skip_notes",
            action="store_false",
            default=None,
            help="DO search through associated notes",
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

        # NOTE: we ignore coverage below because the CI has an additional job running the unittests
        # without optional dependencies available.
        if largs.fuzziness > 0 and not HAS_OPTIONAL_REGEX:  # pragma: no branch
            LOGGER.warning(  # pragma: no cover
                "Using the `--fuzziness` argument requires the optional `regex` dependency to be "
                "installed! Falling back to `fuzziness=0`."
            )
            largs.fuzziness = 0  # pragma: no cover

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

        decode_latex = config.commands.search.decode_latex
        if self.largs.decode_latex is not None:
            decode_latex = self.largs.decode_latex
        LOGGER.debug("The search will%s decode all LaTeX sequences", "" if decode_latex else " NOT")

        decode_unicode = config.commands.search.decode_unicode
        if self.largs.decode_unicode is not None:
            decode_unicode = self.largs.decode_unicode
        LOGGER.debug(
            "The search will%s decode all Unicode characters", "" if decode_unicode else " NOT"
        )

        skip_files = config.commands.search.skip_files
        if self.largs.skip_files is not None:
            skip_files = self.largs.skip_files
        LOGGER.debug(
            "The search will%s look through associated files", " NOT" if skip_files else ""
        )

        skip_notes = config.commands.search.skip_notes
        if self.largs.skip_notes is not None:
            skip_notes = self.largs.skip_notes
        LOGGER.debug(
            "The search will%s look through associated notes", " NOT" if skip_notes else ""
        )

        progress_bar = Progress.initialize()
        optional_awaitable = progress_bar.start()
        if optional_awaitable is not None:
            await optional_awaitable

        task = progress_bar.add_task("Searching...", total=len(self.entries))

        if ignore_case and not skip_files:
            LOGGER.warning(
                "The `--ignore-case` argument does NOT get forwarded to the external grep tool "
                "which is used for searching associated files! Configure its additional arguments "
                "manually via `config.commands.search.grep_args`."
            )

        for entry in self.entries.copy():
            progress_bar.advance(task, 1)
            await asyncio.sleep(0)

            matches = entry.search(
                self.largs.query,
                context=self.largs.context,
                skip_files=skip_files,
                skip_notes=skip_notes,
                ignore_case=ignore_case,
                decode_unicode=decode_unicode,
                decode_latex=decode_latex,
                fuzziness=self.largs.fuzziness,
            )
            if not matches:
                self.entries.remove(entry)
                continue

            self.matches.append(matches)
            self.hits += len(matches)

            LOGGER.debug('Entry "%s" includes %d hits.', entry.label, len(matches))

        progress_bar.stop()

        Event.PostSearchCommand.fire(self)

        if len(self.matches) == 0:
            LOGGER.warning("The search for %s returned no results!", self.largs.query)

    @override
    def render_porcelain(self) -> list[str]:
        output = []
        for entry, matches in zip(self.entries, self.matches):
            title = f"{entry.label}::{len(matches)}"
            output.append(title)

            for idx, match_ in enumerate(matches):
                prefix = f"{idx + 1}::"
                if match_.source:
                    prefix += f"{match_.source}::"
                for line in match_.text.splitlines():
                    output.append(prefix + line.strip())

        return output

    @override
    def render_rich(self) -> ConsoleRenderable:
        tree = Tree(".", hide_root=True)
        for entry, matches in zip(self.entries, self.matches):
            subtree = tree.add(
                Text.from_markup(
                    f"[search.label]{entry.markup_label()}[/search.label] - {len(matches)} match"
                    + ("es" if len(matches) > 1 else "")
                )
            )

            for idx, match_ in enumerate(matches):
                matchtree = subtree.add(f"{idx + 1}: {match_.source}")
                for line in match_.stylize().split():
                    matchtree.add(line)

        return tree

    @override
    def render_textual(self) -> SearchView:
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

            for idx, match_ in enumerate(matches):
                matchtree = subtree.add(
                    f"{idx + 1}: {match_.source}",
                    data=data,
                    expand=not config.tui.tree_folding[1],
                )
                for line in match_.stylize().split():
                    matchtree.add_leaf(line, data=data)

        return tree
