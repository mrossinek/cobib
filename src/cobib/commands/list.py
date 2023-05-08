r"""coBib's List command.

This command simply lists the entries in the database:
```
cobib list
```

### Basic Options

It provides some very basic output manipulation options.

You can reverse the output:
```
cobib list --reverse
```
You can sort the list according to a database field:
```
cobib list --sort year
```
(In the TUI, this is available via the `s` key, by default.)


### Filters

However, the arguably most useful feature of this command are the *filters*.
These are a set of keyword arguments which are registered at runtime depending on the fields which
appear in your database.
To give an example, you can find the following filters in the output of `cobib list --help`:
```
++author AUTHOR
--author AUTHOR
++year YEAR
--year YEAR
```
As you can see, each field is used twice: once with a `++` and once with a `--` prefix.
These allow you to specify positive and negative matches, respectively.
For example:
```
cobib list ++year 2020
```
will list *only* entries whose `year` contains `2020`.
On the contrary:
```
cobib list --year 2020
```
will print all those entries whose `year` does *not* contain `2020`.

You can combine multiple filters to narrow your selection down further.
For example:
```
cobib list ++year 2020 ++author Rossmannek
```
will list entries whose `year` contains `2020` *and* whose `author` field contains `Rossmannek`.

Note, that you by default you can use the `f` key in the TUI to add filters to displayed list of
entries.

There are some aspects to take note of here:
1. By default, multiple filters are combined with logical `AND`s. You can specify `--or` to
   overwrite this to logical `OR`s. This will also apply to all filters of the specified command.
2. All entries are treated as `str`. Thus, `++year 20` will match anything *containing* `20`.

As of version v3.2.0, the filter arguments are evaluated as regex patterns allowing you to do things
like the following:
```
cobib list ++label "\D+_\d+"
```
This will list all entries whose labels are formatted as `"<non-digit characters>_<digits>"`.
"""

from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from rich.console import ConsoleRenderable
from rich.table import Table
from rich.text import Text
from textual.widgets import DataTable

from cobib.config import Event, config
from cobib.database import Database, Entry

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class ListCommand(Command):
    """The List Command."""

    name = "list"

    def __init__(self, args: List[str]) -> None:
        """TODO."""
        super().__init__(args)

        self.entries: List[Entry] = []
        self.columns: List[str] = []

    @classmethod
    def init_argparser(cls) -> None:
        """TODO."""
        parser = ArgumentParser(
            prog="list", description="List subcommand parser.", prefix_chars="+-"
        )
        parser.add_argument("-s", "--sort", help="specify column along which to sort the list")
        parser.add_argument(
            "-r", "--reverse", action="store_true", help="reverses the listing order"
        )
        parser.add_argument(
            "-i", "--ignore-case", action="store_true", help="ignore case for entry matching"
        )
        parser.add_argument(
            "-x",
            "--or",
            dest="OR",
            action="store_true",
            help="concatenate filters with OR instead of AND",
        )
        unique_keys: Set[str] = {"label"}
        LOGGER.debug("Gathering possible filter arguments.")
        for entry in Database().values():
            unique_keys.update(entry.data.keys())
        for key in sorted(unique_keys):
            parser.add_argument(
                "++" + key, type=str, action="append", help="include elements with matching " + key
            )
            parser.add_argument(
                "--" + key, type=str, action="append", help="exclude elements with matching " + key
            )

        cls.argparser = parser

    @classmethod
    def _parse_args(cls, args: List[str]) -> argparse.Namespace:
        """TODO."""
        if "--" in args:
            args.remove("--")  # pragma: no cover

        return super()._parse_args(args)

    def execute(self) -> None:
        """Lists the entries in the database.

        This command simply lists the labels and titles of the entries in the database.
        By default, it lists them in the order in which they appear in the database.
        However, the order as well as selection of entries to be listed can be configured through
        additional arguments.
        Please refer to the [Filters](#filters) section above for more information.
        Note, that the filtering mechanisms leverages `cobib.database.Entry.matches` to do the
        actual filter-matching.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `-r`, `--reverse`: if specified, the entries will be listed in reverse order.
                      This is especially useful in the TUI (where it is enabled by default) because
                      it puts the last added entries at the top of the window. When using the
                      command-line interface it is disabled by default, because this puts the last
                      added entries at the bottom, just above the new command-line prompt.
                    * `-x`, `--or`: if specified, multiple filters will be combined with logical OR
                      rather than the default logical AND.
                    * `-i`, `--ignore-case`: if specified, the entry matching will be case
                      *in*sensitive. You can enable this setting permanently with
                      `config.commands.list.ignore_case`.
                    * `-s`, `--sort`: you can specify an arbitrary `cobib.database.Entry.data` field
                      name which should be used for sorting the listed entries. This will
                      automatically include a column for this field in the output table.
                    * in addition to the options above, [Filter keyword arguments](#filters) are
                      registered at runtime based on the fields available in the database. Please
                      refer the that section for more information.

        Returns:
            A list with the filtered and sorted labels.
        """
        LOGGER.debug("Starting List command.")

        Event.PreListCommand.fire(self)

        filtered_entries, filtered_keys = self.filter_entries()

        self.entries = self._sort_entries(filtered_entries, self.largs.sort, self.largs.reverse)

        # construct list of columns to be displayed
        self.columns = config.commands.list.default_columns
        # display the column along which was sorted
        if self.largs.sort and self.largs.sort not in self.columns:
            self.columns.append(self.largs.sort)
        # also display the keys which were used to filter
        self.columns.extend(col for col in filtered_keys if col not in self.columns)

        Event.PostListCommand.fire(self)

    def filter_entries(self) -> Tuple[List[Entry], Set[str]]:
        """TODO."""
        LOGGER.debug("Constructing filter.")

        filtered_keys: Set[str] = set()
        _filter: Dict[Tuple[str, bool], List[Any]] = defaultdict(list)

        for key, val in self.largs.__dict__.items():
            if key in ["OR", "sort", "reverse", "ignore_case"] or val is None:
                # ignore special arguments
                continue

            # track the keys being filtered to display these columns later
            filtered_keys.add(key)

            if not isinstance(val, list):
                val = [val]
            # iterate values to be filtered by
            for i in val:
                for idx, obj in enumerate(self.args):
                    if i == obj:
                        # once we find the current value in the CLI argument list we can determine
                        # whether this filter is INclusive (`++`) or EXclusive (`--`)
                        index: Tuple[str, bool] = (key, self.args[idx - 1][0] == "+")
                        _filter[index].append(i)
                        break

        LOGGER.debug("Final filter configuration: %s", dict(_filter))

        if self.largs.OR:
            LOGGER.debug("Filters are combined with logical ORs!")

        ignore_case = config.commands.list.ignore_case or self.largs.ignore_case

        for key, entry in Database().items():
            if entry.matches(_filter, self.largs.OR, ignore_case):
                LOGGER.debug('Entry "%s" matches the filter.', key)
                self.entries.append(entry)

        return self.entries, filtered_keys

    @staticmethod
    def _sort_entries(
        entries: List[Entry], sort: Optional[str] = None, reverse: bool = False
    ) -> List[Entry]:
        """TODO."""
        if sort is None:
            if reverse:
                return entries[::-1]
            return entries

        sorted_entries: List[Entry] = sorted(
            entries, reverse=reverse, key=lambda entry: entry.stringify().get(str(sort), "")
        )

        return sorted_entries

    def render_rich(self) -> ConsoleRenderable:
        """TODO."""
        rich_table = Table()

        for col in self.columns:
            rich_table.add_column(col)

        for entry in self.entries:
            stringified: Dict[str, str] = entry.stringify()

            rich_table.add_row(*(stringified.get(col, "") for col in self.columns))

        return rich_table

    def render_textual(self) -> DataTable[Text]:
        """TODO."""
        textual_table: DataTable[Text] = DataTable(id="cobib")
        textual_table.cursor_type = "row"
        textual_table.fixed_columns += 1
        textual_table.zebra_stripes = True
        # TODO: figure out why the following is necessary since the following commit:
        # https://github.com/Textualize/textual/commit/a4252a5760539177f6db8231d4229e8eada923e7
        textual_table.styles.height = "1fr"

        for col in self.columns:
            textual_table.add_column(col, width=None)

        for entry in self.entries:
            stringified: Dict[str, str] = entry.stringify()

            textual_table.add_row(*(Text(stringified.get(col, "")) for col in self.columns))

        return textual_table

    def render_porcelain(self) -> List[str]:
        """TODO."""
        output: List[str] = []

        output.append("::".join(self.columns))

        for entry in self.entries:
            stringified: Dict[str, str] = entry.stringify()

            output.append("::".join(stringified.get(col, "") for col in self.columns))

        return output
