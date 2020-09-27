"""CoBib edit command."""

import argparse
import logging
import os
import sys
import tempfile

from cobib.config import CONFIG
from cobib.database import read_database
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class EditCommand(Command):
    """Edit Command."""

    name = 'edit'

    def execute(self, args, out=sys.stdout):
        """Edit entry.

        Opens an existing entry for manual editing.

        Args: See base class.
        """
        LOGGER.debug('Starting Edit command.')
        parser = ArgumentParser(prog="edit", description="Edit subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        try:
            entry = CONFIG.config['BIB_DATA'][largs.label]
            prv = entry.to_yaml()
        except KeyError:
            # TODO we could handle this case as an addition of a new entry rather than exiting
            msg = f"No entry with the label '{largs.label}' could be found."
            print("Error: " + msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        LOGGER.debug('Creating temporary file.')
        tmp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml')
        tmp_file.write(prv)
        tmp_file.flush()
        LOGGER.debug('Starting editor "%s".', os.environ['EDITOR'])
        status = os.system(os.environ['EDITOR'] + ' ' + tmp_file.name)
        assert status == 0
        LOGGER.debug('Editor finished successfully.')
        with open(tmp_file.name, 'r') as edited:
            nxt = ''.join(edited.readlines()[1:])
        tmp_file.close()
        assert not os.path.exists(tmp_file.name)
        if prv == nxt:
            LOGGER.info('No changes detected.')
            return
        conf_database = CONFIG.config['DATABASE']
        file = os.path.expanduser(conf_database['file'])
        with open(file, 'r') as bib:
            lines = bib.readlines()
        entry_to_be_replaced = False
        with open(file, 'w') as bib:
            for line in lines:
                if line.startswith(largs.label + ':'):
                    LOGGER.debug('Entry "%s" found. Starting to replace lines.', largs.label)
                    entry_to_be_replaced = True
                    continue
                if entry_to_be_replaced and line.startswith('...'):
                    LOGGER.debug('Reached end of entry "%s".', largs.label)
                    entry_to_be_replaced = False
                    bib.writelines(nxt)
                    continue
                if not entry_to_be_replaced:
                    bib.write(line)
        # update bibliography data
        read_database()

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Edit command triggered from TUI.')
        # get current label
        label, _ = tui.get_current_label()
        # populate buffer with entry data
        EditCommand().execute([label])
        # redraw total screen after closing external editor
        LOGGER.debug('Manually redrawing TUI to clear out any editor artefacts.')
        tui.resize_handler(None, None)
        # update database list
        tui.update_list()
