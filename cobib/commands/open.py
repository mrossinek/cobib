"""CoBib open command."""

import argparse
import logging
import os
import subprocess
import sys
from urllib.parse import urlparse

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class OpenCommand(Command):
    """Open Command."""

    name = 'open'

    def execute(self, args, out=sys.stderr):
        """Open file from entries.

        Opens the associated file of the entries with xdg-open.

        Args: See base class.
        """
        LOGGER.debug('Starting Open command.')
        parser = ArgumentParser(prog="open", description="Open subcommand parser.")
        parser.add_argument("labels", type=str, nargs='+', help="labels of the entries")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return None

        errors = []
        for label in largs.labels:
            try:
                entry = CONFIG.config['BIB_DATA'][label]
                if 'file' not in entry.data.keys() or entry.data['file'] is None:
                    msg = "Error: There is no file associated with this entry."
                    LOGGER.error(msg)
                    if out is None:
                        errors.append(msg)
                    continue
                opener = CONFIG.config['DATABASE'].get('open', None)
                try:
                    LOGGER.debug('Parsing "%s" for URLs.', entry.data['file'])
                    url = urlparse(entry.data['file'])
                    if url.scheme:
                        # actual URL
                        url = url.geturl()
                    else:
                        # assume we are talking about a file and thus get its absolute path
                        url = os.path.abspath(url.geturl())
                    LOGGER.debug('Opening "%s" with %s.', url, opener)
                    with open(os.devnull, 'w') as devnull:
                        subprocess.Popen([opener, url], stdout=devnull, stderr=devnull,
                                         stdin=devnull, close_fds=True)
                except FileNotFoundError as err:
                    LOGGER.error(err)
                    errors.append(str(err))
            except KeyError:
                msg = "Error: No entry with the label '{}' could be found.".format(label)
                LOGGER.error(msg)

        return '\n'.join(errors)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Open command triggered from TUI.')
        if tui.selection:
            # use selection for command
            labels = list(tui.selection)
        else:
            # get current label
            label, _ = tui.get_current_label()
            labels = [label]
        # populate buffer with entry data
        error = OpenCommand().execute(labels, out=None)
        if error:
            tui.prompt_print(error)
