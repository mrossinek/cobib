r"""coBib's List command.

This command simply lists the entries in the database:
```
cobib list
```
By default, it lists them in the order in which they appear in the database. However, the order as
well as selection of entries to be listed can be manipulated via additional arguments as explained
below.

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

You can limit the number of displayed entries:
```
cobib list --limit 5
```


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

Note, that by default you can use the `f` key in the TUI to add filters to the displayed list of
entries.

There are some aspects to take note of here:
1. By default, multiple filters are combined with logical `AND`s. You can specify `--or` to
   overwrite this to logical `OR`s. This will apply to all filters of the specified command.
2. All entries are treated as `str`. Thus, `++year 20` will match anything *containing* `20`.

As of version v3.2.0, the filter arguments are evaluated as regex patterns allowing you to do things
like the following:
```
cobib list ++label "\D+_\d+"
```
This will list all entries whose labels are formatted as `"<non-digit characters>_<digits>"`.

As of version v4.0.0, you can make the filter matching case-**in**sensitive via the
`cobib.config.config.ListCommandConfig.ignore_case` setting which defaults to being `False`.
Besides this setting, you can always overwrite its value on the command line with the
`--ignore-case` (`-i` for short) and `--no-ignore-case` (`-I` for short; since v4.1.0) options.
Providing these options takes precedence over your configuration value.
Thus, the following will *always* still match entries where `Rossmannek` is contained in the author
field:
```
cobib list --ignore-case ++author rossmannek
```
And the following will *always* be sensitive to case:
```
cobib list --no-ignore-case ++author rossmannek
```


### Approximate matching

.. note::
   New in version v5.1.0

Besides case-insensitive filter matching (see above), coBib now also provides more means to perform
approximate matching of your filters.

The `--decode-latex` argument will convert LaTeX sequences to Unicode characters (where possible).
For example, a LaTeX-encoded Umlaut like `\"o` will become `ö`. This can significantly simplify your
match query, for example:
```
cobib list --decode-latex ++title Körper
```
will match entries whose title contains `K{\"o}rper`.
You can enable this behavior by default by setting `config.commands.list_.decode_latex = True`.
If you have enabled this setting, you can temporarily overwrite it from the command-line with the
`--no-decode-latex` argument.

Additionally, you can convert Unicode characters to a close ASCII equivalent with `--decode-unicode`
which can simplify your search further. Reusing the example above, you can now match titles
containing `K{\"o}rper` as follows:
```
cobib list --decode-latex --decode-unicode ++title Korper
```
You can enable this behavior by default by setting `config.commands.list_.decode_unicode = True`.
If you have enabled this setting, you can temporarily overwrite it from the command-line with the
`--no-decode-unicode` argument.

Finally, if you install the optional [`regex`](https://pypi.org/project/regex/) dependency you can
even perform fuzzy matching. For example, you can specify the amount of fuzzy errors to allow via
the `--fuzziness` (`-z` for short) argument. Reusing the sample example again, you can allow for
typos in your filter like so:
```
cobib list --decode-latex --decode-unicode --fuzziness 2 ++title Koprer
```
You can specify a default amount of fuzzy errors by setting `config.commands.list_.fuzziness` to the
desired value.


.. note::
   For more information on the filtering mechanisms see also `cobib.database.entry.Entry.matches`.
"""

from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from copy import copy
from typing import Any, Final, Literal, get_args

from rich.console import ConsoleRenderable
from rich.table import Table
from rich.text import Text
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.ui.components import ListView
from cobib.utils.regex import HAS_OPTIONAL_REGEX

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ListCommand(Command):
    """The List Command.

    This command can parse the following arguments:

        * `-s`, `--sort`: you can specify an arbitrary `cobib.database.Entry.data` field name which
          should be used for sorting the listed entries. This will automatically include a column
          for this field in the output table.
        * `-r`, `--reverse`: if specified, the entries will be listed in reverse order. This is
          especially useful in the TUI (where it is enabled by default) because it puts the last
          added entries at the top of the window. When using the command-line interface it is
          disabled by default, because this puts the last added entries at the bottom, just above
          the new command-line prompt.
        * `-l`, `--limit`: you can specify a maximum number of entries to be returned in order to
          limit the amount of matches to be displayed. (Note, that as of now, this is purely a
          post-processing step and, thus, does not yield faster results.)
        * `-i`, `--ignore-case`: if specified, the entry matching will be case-**in**sensitive. This
          overwrites the `cobib.config.config.ListCommandConfig.ignore_case` setting.
        * `-I`, `--no-ignore-case`: if specified, the entry matching will be case-sensitive. This
          overwrites the `cobib.config.config.ListCommandConfig.ignore_case` setting.
        * `--decode-latex`: if specified, all LaTeX sequences will be decoded before matching. This
          overwrites the `cobib.config.config.ListCommandConfig.decode_latex` setting.
        * `--no-decode-latex`: if specified, LaTeX sequences will be left unchanged before matching.
          This overwrites the `cobib.config.config.ListCommandConfig.decode_latex` setting.
        * `--decode-unicode`: if specified, all Unicode characters will be decoded before matching.
          This overwrites the `cobib.config.config.ListCommandConfig.decode_unicode` setting.
        * `--no-decode-unicode`: if specified, Unicode characters will be left unchanged before
          matching. This overwrites the `cobib.config.config.ListCommandConfig.decode_unicode`
          setting.
        * `-z`, `--fuzziness`: you can specify the number of fuzzy errors to allow for entry
          matching. This requires the optional `regex` dependency to be installed.
        * `-x`, `--or`: if specified, multiple filters will be combined with logical OR rather than
          the default logical AND.
        * in addition to the options above, [Filter keyword arguments](#filters) are registered at
          runtime based on the fields available in the database. Please refer that section or the
          output of `cobib list --help` for more information.
    """

    name = "list"

    _RESERVED_FIELDS = Final[
        Literal[
            "OR",
            "sort",
            "reverse",
            "limit",
            "ignore_case",
            "decode_latex",
            "decode_unicode",
            "fuzziness",
        ]
    ]
    """These fields are reserved because they correspond to the names of the command-line arguments.
    This list of values is used when constructing the filter during `filter_entries`."""

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.entries: list[Entry] = []
        """A list of entries, filtered and sorted according to the provided command arguments."""

        self.columns: list[str] = []
        """A list of (key) columns to be included when rendering the results."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="list",
            description="List subcommand parser.",
            prefix_chars="+-",
            exit_on_error=True,
        )
        parser.add_argument("-s", "--sort", help="specify column along which to sort the list")
        parser.add_argument(
            "-r", "--reverse", action="store_true", help="reverses the listing order"
        )
        parser.add_argument("-l", "--limit", type=int, help="limits the number of listed entries")
        ignore_case_group = parser.add_mutually_exclusive_group()
        ignore_case_group.add_argument(
            "-i",
            "--ignore-case",
            action="store_true",
            default=None,
            help="ignore case for entry matching",
        )
        ignore_case_group.add_argument(
            "-I",
            "--no-ignore-case",
            dest="ignore_case",
            action="store_false",
            default=None,
            help="do NOT ignore case for entry matching",
        )
        latex_group = parser.add_mutually_exclusive_group()
        latex_group.add_argument(
            "--decode-latex",
            action="store_true",
            default=None,
            help="decode LaTeX sequences for entry matching",
        )
        latex_group.add_argument(
            "--no-decode-latex",
            dest="decode_latex",
            action="store_false",
            default=None,
            help="do NOT decode LaTeX sequences for entry matching",
        )
        unicode_group = parser.add_mutually_exclusive_group()
        unicode_group.add_argument(
            "--decode-unicode",
            action="store_true",
            default=None,
            help="decode Unicode characters for entry matching",
        )
        unicode_group.add_argument(
            "--no-decode-unicode",
            dest="decode_unicode",
            action="store_false",
            default=None,
            help="do NOT decode Unicode characters for entry matching",
        )
        parser.add_argument(
            "-z",
            "--fuzziness",
            type=int,
            default=config.commands.list_.fuzziness,
            help=(
                "how many fuzzy errors to allow for entry matching. This requires the optional "
                "`regex` dependency to be installed."
            ),
        )
        parser.add_argument(
            "-x",
            "--or",
            dest="OR",
            action="store_true",
            help="concatenate filters with OR instead of AND",
        )
        unique_keys: set[str] = {"label"}
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

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        args = tuple(arg for arg in args if arg != "--")

        largs = super()._parse_args(args)

        if largs.fuzziness > 0 and not HAS_OPTIONAL_REGEX:  # pragma: no branch
            LOGGER.warning(  # pragma: no cover
                "Using the `--fuzziness` argument requires the optional `regex` dependency to be "
                "installed! Falling back to `fuzziness=0`."
            )
            largs.fuzziness = 0  # pragma: no cover

        return largs

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting List command.")

        Event.PreListCommand.fire(self)

        self.entries, filtered_keys = self.execute_dull()

        # construct list of columns to be displayed
        self.columns = copy(config.commands.list_.default_columns)
        LOGGER.debug("Listing the default columns: %s", str(self.columns))
        # display the column along which was sorted
        if self.largs.sort and self.largs.sort not in self.columns:
            LOGGER.debug("Appending the column which is sorted by: %s", str(self.largs.sort))
            self.columns.append(self.largs.sort)
        # also display the keys which were used to filter
        LOGGER.debug("Extendings the columns which are filtered by: %s", str(filtered_keys))
        self.columns.extend(col for col in filtered_keys if col not in self.columns)

        Event.PostListCommand.fire(self)

    def execute_dull(self) -> tuple[list[Entry], set[str]]:
        """The event-less variant of `execute`.

        This method executes this command without firing any events or post-processing the final
        list of labels. This can be used by other commands which allow piping of the filtering/
        sorting/limiting arguments to the `ListCommand`.

        Returns:
            A pair of the filtered, sorted, and limited entries as the first object (which is also
            exposed via `entries`) and the set of keys which were filtered on as the second one.
            This can be used (for example) to include these keys during the result rendering.
        """
        _, filtered_keys = self.filter_entries()

        sorted_entries = self.sort_entries()

        self.entries = sorted_entries[: self.largs.limit]

        return self.entries, filtered_keys

    def filter_entries(self) -> tuple[list[Entry], set[str]]:
        """The filtering method.

        This method implements the actual filtering routine. Based on the arguments provided to this
        command, this method will iterate the database and return those entries which match the
        specified filter.

        Returns:
            A pair indicating the matching entries. The first object is the list of matching entries
            (which is also exposed via `entries`). The second object is the set of keys which were
            filtered on. This can be used (for example) to include these keys during the result
            rendering.
        """
        LOGGER.debug("Constructing filter.")

        filtered_keys: set[str] = set()
        _filter: dict[tuple[str, bool], list[Any]] = defaultdict(list)

        for key, val in self.largs.__dict__.items():
            # we use get_args twice:
            #  1. to extract the args from `Final`
            #  2. and then to extract the args from the `Literal` stored in the first arg of `Final`
            if key in get_args(get_args(self._RESERVED_FIELDS)[0]) or val is None:
                # ignore special arguments
                continue

            # track the keys being filtered to display these columns later
            filtered_keys.add(key)

            if not isinstance(val, list):
                val = [val]  # noqa: PLW2901
            # iterate values to be filtered by
            for i in val:
                for idx, obj in enumerate(self.args):
                    if i == obj:
                        # once we find the current value in the CLI argument list we can determine
                        # whether this filter is INclusive (`++`) or EXclusive (`--`)
                        index: tuple[str, bool] = (key, self.args[idx - 1][0] == "+")
                        _filter[index].append(i)
                        break

        LOGGER.debug("Final filter configuration: %s", dict(_filter))

        if self.largs.OR:
            LOGGER.debug("Filters are combined with logical ORs!")

        ignore_case = config.commands.list_.ignore_case
        if self.largs.ignore_case is not None:
            ignore_case = self.largs.ignore_case
        LOGGER.debug(
            "The entry matching will be performed case %ssensitive", "in" if ignore_case else ""
        )

        decode_latex = config.commands.list_.decode_latex
        if self.largs.decode_latex is not None:
            decode_latex = self.largs.decode_latex
        LOGGER.debug(
            "The entry matching will%s decode all LaTeX sequences", "" if decode_latex else " NOT"
        )

        decode_unicode = config.commands.list_.decode_unicode
        if self.largs.decode_unicode is not None:
            decode_unicode = self.largs.decode_unicode
        LOGGER.debug(
            "The entry matching will%s decode all Unicode characters",
            "" if decode_unicode else " NOT",
        )

        if len(filtered_keys) == 0:
            # bypassing the unnecessary calls to `Entry.matches` when no filter was provided
            self.entries = list(Database().values())
        else:
            for key, entry in Database().items():
                if entry.matches(
                    _filter,
                    self.largs.OR,
                    ignore_case=ignore_case,
                    decode_latex=decode_latex,
                    decode_unicode=decode_unicode,
                    fuzziness=self.largs.fuzziness,
                ):
                    LOGGER.debug('Entry "%s" matches the filter.', key)
                    self.entries.append(entry)

        return self.entries, filtered_keys

    def sort_entries(self) -> list[Entry]:
        """The sorting method.

        This method sorts the entries according to the key and order provided to this command.
        This method _must_ be run after `filter_entries` to ensure that the `entries` of this
        command instance are already populated.

        Returns:
            The sorted list of entries.
        """
        if self.largs.reverse:
            LOGGER.debug("Reversing the entry order.")

        if self.largs.sort is None:
            if self.largs.reverse:
                self.entries = self.entries[::-1]
            return self.entries

        LOGGER.debug("Sorting entries by key '%s'.", self.largs.sort)

        self.entries = sorted(
            self.entries,
            reverse=self.largs.reverse,
            key=lambda entry: entry.stringify().get(str(self.largs.sort), ""),
        )

        return self.entries

    @override
    def render_porcelain(self) -> list[str]:
        output: list[str] = []

        output.append("::".join(self.columns))

        for entry in self.entries:
            stringified: dict[str, str] = entry.stringify()

            output.append("::".join(stringified.get(col, "") for col in self.columns))

        return output

    @override
    def render_rich(self) -> ConsoleRenderable:
        rich_table = Table()

        for col in self.columns:
            rich_table.add_column(col)

        for entry in self.entries:
            stringified: dict[str, str] = entry.stringify(markup=True)

            rich_table.add_row(*(stringified.get(col, "") for col in self.columns))

        return rich_table

    @override
    def render_textual(self) -> ListView:
        textual_table = ListView()

        for col in self.columns:
            textual_table.add_column(col, width=None)

        for entry in self.entries:
            stringified: dict[str, str] = entry.stringify(markup=True)

            textual_table.add_row(
                *(Text.from_markup(stringified.get(col, "")) for col in self.columns),
                key=entry.label,
            )

        return textual_table
