"""Cobib init command"""

import argparse
import sys
import textwrap
from collections import defaultdict
from operator import itemgetter

from .base_command import ArgumentParser, Command


class ListCommand(Command):
    """List Command"""

    name = 'list'

    # pylint: disable=too-many-branches,too-many-locals,arguments-differ
    def execute(self, args, out=sys.stdout):
        """list entries

        By default, all entries of the database are listed.
        This output will be filterable in the future by providing values for any
        set of table keys.
        """
        if '--' in args:
            args.remove('--')
        parser = ArgumentParser(prog="list", description="List subcommand parser.",
                                prefix_chars='+-')
        parser.add_argument('-x', '--or', dest='OR', action='store_true',
                            help="concatenate filters with OR instead of AND")
        parser.add_argument('-l', '--long', action='store_true',
                            help="print table in long format (i.e. wrap and don't shorten lines)")
        parser.add_argument('-s', '--sort', help="specify column along which to sort the list")
        parser.add_argument('-r', '--reverse', action='store_true',
                            help="reverses the sorting order")
        bib_data = self._read_database()
        unique_keys = set()
        for entry in bib_data.values():
            unique_keys.update(entry.data.keys())
        for key in sorted(unique_keys):
            parser.add_argument('++'+key, type=str, action='append',
                                help="include elements with matching "+key)
            parser.add_argument('--'+key, type=str, action='append',
                                help="exclude elements with matching "+key)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return None

        _filter = defaultdict(list)
        for key, val in largs.__dict__.items():
            if key in ['OR', 'long', 'sort', 'reverse'] or val is None:
                continue
            if not isinstance(val, list):
                val = [val]
            for i in val:
                for idx, obj in enumerate(args):
                    if i == obj:
                        _filter[tuple([key, args[idx-1][0] == '+'])].append(i)
                        break
        columns = ['ID', 'title']
        if largs.sort and largs.sort not in columns:
            # insert columns which are sorted by at front of list view
            columns.insert(1, largs.sort)
        # filtered columns are still appended
        columns.extend([arg[0] for arg in _filter.keys() if arg[0] not in columns])
        widths = [0]*len(columns)
        labels = []
        table = []
        for key, entry in bib_data.items():
            if entry.matches(_filter, largs.OR):
                labels.append(key)
                table.append([entry.data.get(c, '') for c in columns])
                if largs.long:
                    table[-1][1] = table[-1][1]
                else:
                    table[-1][1] = textwrap.shorten(table[-1][1], 80, placeholder='...')
                widths = [max(widths[col], len(table[-1][col])) for col in range(len(widths))]
        if largs.sort:
            table = sorted(table, key=itemgetter(columns.index(largs.sort)), reverse=largs.reverse)
        for row in table:
            print('  '.join([f'{col: <{wid}}' for col, wid in zip(row, widths)]), file=out)
        return labels

    @staticmethod
    def tui(tui, sort_mode):
        """TUI command interface"""
        tui.buffer.clear()
        # update list prompt arguments
        if sort_mode:
            try:
                sort_arg_idx = tui.list_args.index('-s')
                tui.list_args.pop(sort_arg_idx+1)
                tui.list_args.pop(sort_arg_idx)
            except ValueError:
                pass
            tui.list_args += ['-s']
        # handle input via prompt
        command = tui.prompt_handler('list ' + ' '.join(tui.list_args), out=tui.buffer)
        # after the command has been executed n the prompt handler, the `command` variable will
        # contain the contents of the prompt
        if command:
            if sort_mode:
                try:
                    sort_arg_idx = command.index('-s')
                    if sort_arg_idx+1 >= len(command):
                        raise ValueError
                    tui.list_args += [command[sort_arg_idx+1]]
                except ValueError:
                    tui.list_args.remove('-s')
            else:
                # first, pop all filters from tui.list_args
                indices_to_pop = []
                # enumerate words in current list arguments
                prev_args = list(enumerate(tui.list_args))
                # iterate in reverse to ensure popping indices remain correct after popping a few
                prev_args.reverse()
                for idx, p_arg in prev_args:
                    if p_arg[:2] in ('++', '--'):
                        # matches a filter: current index is type and one larger is the key
                        indices_to_pop.extend([idx+1, idx])
                for idx in indices_to_pop:
                    tui.list_args.pop(idx)
                # then, add all new filter (type, key) pairs
                for idx, n_arg in enumerate(command):
                    if n_arg[:2] in ('++', '--'):
                        tui.list_args.extend(command[idx:idx+2])
        # populate buffer with the list
        tui.list_mode = -1
        tui.inactive_commands = []
        tui.buffer.view(tui.viewport, tui.visible, tui.width-1)
        # update database list
        tui.update_list()
