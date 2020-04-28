"""CoBib edit command"""

import argparse
import os
import sys
import tempfile

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command


class EditCommand(Command):
    """Edit Command"""

    name = 'edit'

    def execute(self, args, out=sys.stdout):  # pylint: disable=too-many-locals
        """edit entry

        Opens an existing entry for manual editing.
        """
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
            print("Error: No entry with the label '{}' could be found.".format(largs.label))
        tmp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml')
        tmp_file.write(prv)
        tmp_file.flush()
        status = os.system(os.environ['EDITOR'] + ' ' + tmp_file.name)
        assert status == 0
        tmp_file.seek(0, 0)
        nxt = ''.join(tmp_file.readlines()[1:])
        tmp_file.close()
        assert not os.path.exists(tmp_file.name)
        if prv == nxt:
            return
        conf_database = CONFIG.config['DATABASE']
        file = os.path.expanduser(conf_database['file'])
        with open(file, 'r') as bib:
            lines = bib.readlines()
        entry_to_be_replaced = False
        with open(file, 'w') as bib:
            for line in lines:
                if line.startswith(largs.label):
                    entry_to_be_replaced = True
                    continue
                if entry_to_be_replaced and line.startswith('...'):
                    entry_to_be_replaced = False
                    bib.writelines(nxt)
                    continue
                if not entry_to_be_replaced:
                    bib.write(line)

    @staticmethod
    def tui(tui):
        """TUI command interface"""
        # get current label
        label = tui.get_current_label()
        # populate buffer with entry data
        EditCommand().execute([label])
        # redraw total screen after closing external editor
        tui.resize_handler(None, None)
        # update database list
        tui.update_list()
