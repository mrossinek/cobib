"""CoBib open command."""

import argparse
import logging
import os
import subprocess
import sys
from collections import defaultdict
from urllib.parse import urlparse

from cobib.config import config
from cobib.database import Database

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class OpenCommand(Command):
    """Open Command."""

    name = "open"

    # pylint: disable=too-many-branches
    def execute(self, args, out=sys.stderr):
        """Open file from entries.

        Opens the associated file of the entries with xdg-open.

        Args: See base class.
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
            print(exc.message, file=sys.stderr)
            return

        bib = Database()

        # pylint: disable=too-many-nested-blocks
        for label in largs.labels:
            things_to_open = defaultdict(list)
            count = 0
            # first: find all possible things to open
            try:
                entry = bib[label]
                for field in ("file", "url"):
                    if field in entry.data.keys() and entry.data[field]:
                        for val in entry.data[field].split(","):
                            val = val.strip()
                            LOGGER.debug('Parsing "%s" for URLs.', val)
                            things_to_open[field] += [urlparse(val)]
                            count += 1
            except KeyError:
                msg = "No entry with the label '{}' could be found.".format(label)
                LOGGER.warning(msg)
                print(msg, file=sys.stderr)
                continue

            # if there are none, skip current label
            if not things_to_open:
                msg = "The entry '{}' has no actionable field associated with it.".format(label)
                LOGGER.warning(msg)
                print(msg, file=sys.stderr)
                continue

            if count == 1:
                # we found a single URL to open
                self._open_url(list(things_to_open.values())[0][0])
            else:
                # we query the user what to do
                idx = 1
                url_list = []
                prompt = []
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
                        print(msg, file=sys.stderr)
                        break
                    if choice == "help":
                        LOGGER.debug("User requested help.")
                        if not help_requested:
                            msg = [
                                "You can specify one of the following options:",
                                "  1. a url number",
                                "  2. a field name provided in '[...]'",
                                "  3. or simply 'all'",
                                "  4. ENTER will abort the command",
                                "",
                            ]
                            prompt = msg + prompt
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

    @staticmethod
    def _open_url(url):
        """Opens a URL."""
        opener = config.commands.open.command
        try:
            url = url.geturl() if url.scheme else os.path.abspath(url.geturl())
            LOGGER.debug('Opening "%s" with %s.', url, opener)
            with open(os.devnull, "w") as devnull:
                subprocess.Popen(
                    [opener, url], stdout=devnull, stderr=devnull, stdin=devnull, close_fds=True
                )
        except FileNotFoundError as err:
            LOGGER.error(err)
            print(err, file=sys.stderr)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug("Open command triggered from TUI.")
        if tui.selection:
            # use selection for command
            labels = list(tui.selection)
        else:
            # get current label
            label, _ = tui.viewport.get_current_label()
            labels = [label]
        tui.execute_command(["open"] + labels, skip_prompt=True)
