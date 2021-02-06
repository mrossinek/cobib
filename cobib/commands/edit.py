"""CoBib edit command."""

import argparse
import logging
import os
import sys
import tempfile

from cobib.config import config
from cobib.database import Database, Entry
from cobib.parsers import YAMLParser
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
        parser.add_argument("-a", "--add", action='store_true',
                            help="if specified, will add a new entry for unknown labels")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        yml = YAMLParser()

        bib = Database()

        try:
            entry = bib[largs.label]
            prv = yml.dump(entry)
            if largs.add:
                LOGGER.warning("Entry '%s' already exists! Ignoring the `--add` argument.",
                               largs.label)
                largs.add = False
        except KeyError:
            # No entry for given label found
            if largs.add:
                # add a new entry for the unknown label
                entry = Entry(largs.label,
                              {'ID': largs.label,
                               'ENTRYTYPE': config.format.default_entry_type})
                prv = yml.dump(entry)
            else:
                msg = f"No entry with the label '{largs.label}' could be found.\n" \
                    + "Use `--add` to add a new entry with this label."
                LOGGER.error(msg)
                return

        LOGGER.debug('Creating temporary file.')
        tmp_file = tempfile.NamedTemporaryFile(mode='w+', prefix='cobib-', suffix='.yaml')
        tmp_file.write(prv)
        tmp_file.flush()
        LOGGER.debug('Starting editor "%s".', os.environ['EDITOR'])
        status = os.system(os.environ['EDITOR'] + ' ' + tmp_file.name)
        assert status == 0
        LOGGER.debug('Editor finished successfully.')
        new_entries = YAMLParser().parse(tmp_file.name)
        new_entry = new_entries[list(new_entries.keys())[0]]
        tmp_file.close()
        assert not os.path.exists(tmp_file.name)
        if entry == new_entry:
            LOGGER.info('No changes detected.')
            return

        bib.update({new_entry.label: new_entry})
        bib.save()

        self.git(args=vars(largs))

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Edit command triggered from TUI.')
        # get current label
        label, _ = tui.viewport.get_current_label()
        # populate buffer with entry data
        EditCommand().execute([label])
        # redraw total screen after closing external editor
        LOGGER.debug('Manually redrawing TUI to clear out any editor artefacts.')
        tui.resize_handler(None, None)
        # update database list
        tui.viewport.update_list()
