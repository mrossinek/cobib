"""CoBib search command."""

import argparse
import logging
import os
import re
import shlex
import sys

from cobib import __version__
from cobib.config import CONFIG
from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)


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
        parser.add_argument('list_arg', nargs='*',
                            help="Any arguments for the List subcommand." +
                            "\nUse this to add filters to specify a subset of searched entries." +
                            "\nYou can add a '--' before the List arguments to ensure separation." +
                            "\nSee also `list --help` for more information on the List arguments.")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return None

        labels = ListCommand().execute(largs.list_arg, out=open(os.devnull, 'w'))
        LOGGER.debug('Available entries to search: %s', labels)

        ignore_case = CONFIG.config['DATABASE'].getboolean('search_ignore_case', False) or \
            largs.ignore_case
        re_flags = re.IGNORECASE if ignore_case else 0
        LOGGER.debug('The search will be performed case %ssensitive', 'in' if ignore_case else '')

        hits = 0
        output = []
        for label in labels.copy():
            entry = CONFIG.config['BIB_DATA'][label]
            matches = entry.search(largs.query, largs.context, ignore_case)
            if not matches:
                labels.remove(label)
                continue

            hits += len(matches)
            LOGGER.debug('Entry "%s" includes %d hits.', label, hits)
            title = f"{label} - {len(matches)} match" + ("es" if len(matches) > 1 else "")
            title = title.replace(label, CONFIG.get_ansi_color('search_label') + label + '\x1b[0m')
            output.append(title)

            for idx, match in enumerate(matches):
                for line in match:
                    line = re.sub(rf'({largs.query})',
                                  CONFIG.get_ansi_color('search_query') + r'\1' + '\x1b[0m',
                                  line, flags=re_flags)
                    output.append(f"[{idx+1}]\t".expandtabs(8) + line)

        print('\n'.join(output), file=out)
        return (hits, labels)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Search command triggered from TUI.')
        tui.viewport.clear()
        # handle input via prompt
        command, results = tui.execute_command('search', out=tui.viewport.buffer)
        if tui.viewport.buffer.lines and results is not None:
            hits, labels = results
            tui.STATE.mode = 'search'
            cur_y, _ = tui.viewport.pad.getyx()
            tui.STATE.previous_line = cur_y
            tui.viewport.buffer.split()
            LOGGER.debug('Applying selection highlighting in search results.')
            for label in labels:
                if label not in tui.selection:
                    continue
                # we match the label including its 'search_label' highlight to ensure that we really
                # only match this specific occurrence of whatever the label may be
                tui.viewport.buffer.replace(range(tui.viewport.buffer.height),
                                            re.escape(CONFIG.get_ansi_color('search_label'))
                                            + label + re.escape('\x1b[0m'),
                                            CONFIG.get_ansi_color('search_label') +
                                            CONFIG.get_ansi_color('selection')
                                            + label + '\x1b[0m\x1b[0m')
            LOGGER.debug('Populating viewport with search results.')
            tui.viewport.view(ansi_map=tui.ANSI_MAP)
            # reset current cursor position
            LOGGER.debug('Resetting cursor position to top.')
            tui.STATE.top_line = 0
            tui.STATE.current_line = 0
            # update top statusbar
            tui.STATE.topstatus = "CoBib v{} - {} hit{}".format(__version__, hits,
                                                                "s" if hits > 1 else "")
            tui.statusbar(tui.topbar, tui.STATE.topstatus)
            tui.STATE.inactive_commands = ['Add', 'Filter', 'Sort']
        elif command[1:]:
            msg = f"No search hits for '{shlex.join(command[1:])}'!"
            LOGGER.info(msg)
            tui.prompt_print(msg)
            tui.viewport.update_list()
