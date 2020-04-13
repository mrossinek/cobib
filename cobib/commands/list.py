"""Cobib init command"""

import argparse
import sys
import textwrap
from collections import defaultdict
from operator import itemgetter

# third-party
import tabulate

from .base_command import Command


class ListCommand(Command):  # pylint: disable=too-few-public-methods
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
        parser = argparse.ArgumentParser(prog="list", description="List subcommand parser.",
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
        largs = parser.parse_args(args)
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
            columns.append(largs.sort)
        columns.extend([arg[0] for arg in _filter.keys() if arg[0] not in columns])
        labels = []
        table = []
        for key, entry in bib_data.items():
            if entry.matches(_filter, largs.OR):
                labels.append(key)
                table.append([entry.data.get(c, None) for c in columns])
                if largs.long:
                    table[-1][1] = textwrap.fill(table[-1][1], width=80)
                else:
                    table[-1][1] = textwrap.shorten(table[-1][1], 80, placeholder='...')
        if largs.sort:
            table = sorted(table, key=itemgetter(columns.index(largs.sort)), reverse=largs.reverse)
        print(tabulate.tabulate(table, headers=columns), file=out)
        return labels
