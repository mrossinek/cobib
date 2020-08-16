"""CoBib search command."""

import argparse
import logging
import os
import re
import sys

from cobib import __version__
from cobib.config import CONFIG
from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)

ANSI_COLORS = [
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'white',
]

if 'COLORS' not in CONFIG.config.keys():
    CONFIG.config['COLORS'] = {}

SEARCH_LABEL_FG = 30 + ANSI_COLORS.index(CONFIG.config['COLORS'].get('search_label_fg', 'blue'))
SEARCH_LABEL_BG = 40 + ANSI_COLORS.index(CONFIG.config['COLORS'].get('search_label_bg', 'black'))
SEARCH_QUERY_FG = 30 + ANSI_COLORS.index(CONFIG.config['COLORS'].get('search_query_fg', 'red'))
SEARCH_QUERY_BG = 40 + ANSI_COLORS.index(CONFIG.config['COLORS'].get('search_query_bg', 'black'))

SEARCH_LABEL_ANSI = f'\033[{SEARCH_LABEL_FG};{SEARCH_LABEL_BG}m'
SEARCH_QUERY_ANSI = f'\033[{SEARCH_QUERY_FG};{SEARCH_QUERY_BG}m'


class SearchCommand(Command):
    """Search Command."""

    name = 'search'

    def execute(self, args, out=sys.stdout):
        """Search database.

        Searches the database recursively (i.e. including any associated files) using `grep` for a
        query string.

        Args: See base class.
        """
        LOGGER.debug('Starting Search command.')
        parser = ArgumentParser(prog="search", description="Search subcommand parser.")
        parser.add_argument("query", type=str, help="text to search for")
        parser.add_argument("-c", "--context", type=int, default=1,
                            help="number of context lines to provide for each match")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore case for searching")
        parser.add_argument('list_args', nargs='*')

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return None

        labels = ListCommand().execute(largs.list_args, out=open(os.devnull, 'w'))
        LOGGER.debug('Available entries to search: %s', labels)

        re_flags = re.IGNORECASE if largs.ignore_case else 0
        LOGGER.debug('The search will be performed case %ssensitive',
                     'in' if largs.ignore_case else '')

        hits = 0
        output = []
        for label in labels:
            entry = CONFIG.config['BIB_DATA'][label]
            matches = entry.search(largs.query, largs.context, largs.ignore_case)
            if not matches:
                continue

            hits += len(matches)
            LOGGER.debug('Entry "%s" includes %d hits.', label, hits)
            title = f"{label} - {len(matches)} match" + ("es" if len(matches) > 1 else "")
            title = title.replace(label, SEARCH_LABEL_ANSI + label + '\033[0m')
            output.append(title)

            for idx, match in enumerate(matches):
                for line in match:
                    line = re.sub(rf'({largs.query})', SEARCH_QUERY_ANSI + r'\1' + '\033[0m',
                                  line, flags=re_flags)
                    output.append(f"[{idx+1}]\t".expandtabs(8) + line)

        print('\n'.join(output), file=out)
        return hits

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Search command triggered from TUI.')
        tui.buffer.clear()
        # handle input via prompt
        command, hits = tui.prompt_handler('search', out=tui.buffer)
        if tui.buffer.lines:
            tui.list_mode, _ = tui.viewport.getyx()
            tui.buffer.split()
            LOGGER.debug('Populating viewport with search results.')
            ansi_map = {SEARCH_LABEL_ANSI: tui.COLOR_PAIRS['search_label'][0],
                        SEARCH_QUERY_ANSI: tui.COLOR_PAIRS['search_query'][0]}
            LOGGER.debug('Using ANSI color map: %s', ansi_map)
            tui.buffer.view(tui.viewport, tui.visible, tui.width-1, ansi_map)
            # reset current cursor position
            LOGGER.debug('Resetting cursor position to top.')
            tui.top_line = 0
            tui.current_line = 0
            # update top statusbar
            tui.topstatus = "CoBib v{} - {} hit{}".format(__version__, hits,
                                                          "s" if hits > 1 else "")
            tui.statusbar(tui.topbar, tui.topstatus)
        elif command[1:] and not tui.buffer.lines:
            tui.prompt.clear()
            msg = f"No search hits for '{' '.join(command[1:])}'!"
            LOGGER.info(msg)
            tui.prompt.addstr(0, 0, msg)
            tui.prompt.refresh()
            tui.update_list()
