r"""coBib's Modify command.

This command allows you to perform bulk modification to multiple entries.
Thus, it provides faster means to apply simple edits to many entries at once, without having to open
each entry for editing one-by-one or having to edit the database file manually.

It takes a modification in the form `<field>:<value>` and will overwrite the `field` of all matching
entries with the new `value`. A simple example is the following:
```
cobib modify tags:private --selection -- Label1 Label2 ...
```
which will set the tags of all listed entries to `private`.

You can use the `--add` option to not overwrite but append to existing values of a field. `str`
fields will be concatenated with*out* any spaces, lists will be appended, and numeric fields will be
added. Any other kind of field will be converted to a `str`.

As of v4.4.0 you can also use the `--remove` option to achieve the opposite to the above: removing
an item from a list or subtracting numbers. Strings cannot be subtracted and any other kind of field
will log a warning but continue gracefully.

.. note::

   The options `--add` and `--remove` are mutually exclusive for obvious reasons.

As with other commands, you can also use filters (see also `cobib.commands.list_`) rather than a
manual selection to specify the entries which to modify:
```
cobib modify tags:first_author -- ++author Rossmannek
```

As of v3.2.0 the `value` provided as part of the modification is interpreted as an "f"-string.[^1]
This means you can even use placeholder variables and perform simple operations on them. The
available variables depend on the entry which you are modifying as they are inferred from its stored
data.
Below are some examples:
```
# Rewrite the 'pages' field with a single-dash separator
cobib modify "pages:{pages.replace('--', '-')}" -- ...

# Rename an entry according to the first author's surname and year
cobib modify "label:{author.split()[1]}{year}" -- ...
```

In case you are applying a modification to your entry labels, the value of the
`cobib.config.config.ModifyCommandConfig.preserve_files` setting (added in v4.1.0) determines
whether all of your associated files will be renamed accordingly. This defaults to `False`, meaning
that they *will* be renamed. You can overwrite the value of this setting at runtime with the
`--preserve-files` and `--no-preserve-files` arguments, respectively.
I.e. the following will **not** rename your files:
```
# Rename an entry according to the first author's surname and year, but preserve the original file
cobib modify "label:{author.split()[1]}{year}" --preserve-files -- ...
```
While this command will always rename them:
```
# Rename an entry according to the first author's surname and year, and rename the original file
cobib modify "label:{author.split()[1]}{year}" --no-preserve-files -- ...
```

In combination with the regex-support for filters added during the same release, you can even unify
your database's label convention:
```
cobib modify "label:{label.replace('_', '')}" -- ++label "\D+_\d+"
```

If you happen to use an undefined variable as part of your modification, coBib will handle this
gracefully by falling back to an empty string and raising a warning:
```
cobib modify "note:{undefined}" -- ...
> [WARNING] You tried use an undefined variable. Falling back to an empty string.
> [ERROR] name 'undefined' is not defined
```

Since v3.3.0 this command also provides a "dry" mode which previews the modifications without
actually applying them.
```
cobib modify --dry <modification> -- ...
```
This is useful if you want to test large bulk modifications before running them in order to prevent
mistakes.

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `m` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:modify <arguments go here>
```

[^1]: <https://docs.python.org/3/reference/lexical_analysis.html#formatted-string-literals>
"""

from __future__ import annotations

import ast
import logging
from collections.abc import Callable
from copy import copy
from typing import Any

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from text_unidecode import unidecode
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.utils.logging import get_stream_handler
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command
from .list_ import ListCommand

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ModifyCommand(Command):
    """The Modify Command.

    This command can parse the following arguments:

        * `modification`: a string conforming to `<field>:<value>` indicating the modification that
          should be applied to all matching entries. By default, the modification will overwrite any
          existing data in the specified `field` with the new `value`. For more information about
          formatting options of `<value>` refer to the module documentation or the man-page.
        * `--dry`: run in "dry"-mode which lists modifications without applying them.
        * `-a`, `--add`: when specified, the modification's value will be added to the entry's field
          rather than overwrite it. If the field in question is numeric, the numbers will be added.
          This argument is _mutually exclusive_ with `--remove`.
        * `-r`, `--remove`: when specified, the modification's value will be removed from the
          entry's field rather than overwrite it. If the field in question is numeric, the numbers
          will be subtracted. This argument is _mutually exclusive_ with `--add`.
        * `--preserve-files`: skips the renaming of any associated files in case the applied
          modification acted on the entry labels. This overwrites the
          `cobib.config.config.ModifyCommandConfig.preserve_files` setting.
        * `--no-preserve-files`: does NOT skip the renaming of any associated files in case the
          applied modification acted on the entry labels. This overwrites the
          `cobib.config.config.ModifyCommandConfig.preserve_files` setting.
        * `-s`, `--selection`: when specified, the positional arguments will *not* be interpreted as
          filters but rather as a direct list of entry labels. This can be used on the command-line
          but is mainly meant for the TUIs visual selection interface (hence the name).
        * in addition to the above, you can add `filters` to specify a subset of your database for
          exporting. For more information refer to `cobib.commands.list_`.
    """

    name = "modify"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        self.modified_entries: list[Entry] = []
        """A list of `cobib.database.Entry` objects which were modified by this command."""

    @staticmethod
    def field_value_pair(string: str) -> tuple[str, str]:
        """Utility method to assert the field-value pair argument type.

        This method is given to the `argparse.ArgumentParser` instance as its `type` specifier.
        An input argument is considered valid if it passes through this function without raising any
        errors, which means it conforms to the `<field>:<value>` notation.

        Args:
            string: the argument string to check.

        Returns:
            The pair of strings: `field` and `value`.
        """
        # try splitting the string into field and value, any errors will be handled by argparse
        field, *value = string.split(":")
        # NOTE: we split only the first field off in case the value contains f-string format
        # specifications
        return (field, ":".join(value))

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="modify", description="Modify subcommand parser.")
        parser.add_argument(
            "modification",
            type=ModifyCommand.field_value_pair,
            help="Modification to apply to the specified entries."
            "\nThis argument must be a string formatted as <field>:<value> where field can be any "
            "field of the entries and value can be any string which should be placed in that "
            "field. Be sure to escape this field-value pair properly, especially if the value "
            "contains spaces.",
        )
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Run in 'dry'-mode, listing modifications without actually applying them.",
        )
        add_remove = parser.add_mutually_exclusive_group()
        add_remove.add_argument(
            "-a",
            "--add",
            action="store_true",
            help="Adds to the modified field rather than overwriting it.",
        )
        add_remove.add_argument(
            "-r",
            "--remove",
            action="store_true",
            help="Removes from the modified field rather than overwriting it.",
        )
        preserve_files_group = parser.add_mutually_exclusive_group()
        preserve_files_group.add_argument(
            "--preserve-files",
            action="store_true",
            default=None,
            help="do NOT rename associated files",
        )
        preserve_files_group.add_argument(
            "--no-preserve-files",
            dest="preserve_files",
            action="store_false",
            default=None,
            help="rename associated files",
        )
        parser.add_argument(
            "-s",
            "--selection",
            action="store_true",
            help="When specified, the `filter` argument will be interpreted as a list of entry "
            "labels rather than arguments for the `list` command.",
        )
        parser.add_argument(
            "filter",
            nargs="+",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be modified. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:  # noqa: PLR0912, PLR0915
        LOGGER.debug("Starting Modify command.")

        Event.PreModifyCommand.fire(self)

        info_handler: logging.Handler
        if self.largs.dry:
            info_handler = get_stream_handler(logging.INFO)

            class ModifyInfoFilter(logging.Filter):
                """A logging filter to only print ModifyCommand INFO messages."""

                def filter(self, record: logging.LogRecord) -> bool:
                    return record.name == "cobib.commands.modify" and record.levelname == "INFO"

            info_handler.addFilter(ModifyInfoFilter())
            LOGGER.addHandler(info_handler)

        if self.largs.selection:
            LOGGER.info("Selection given. Interpreting `filter` as a list of labels")
            labels = self.largs.filter
        else:
            LOGGER.debug("Gathering filtered list of entries to be modified.")
            listed_entries, _ = ListCommand(*self.largs.filter).execute_dull()
            labels = [entry.label for entry in listed_entries]

        field, value = self.largs.modification

        preserve_files = config.commands.modify.preserve_files
        if self.largs.preserve_files is not None:
            preserve_files = self.largs.preserve_files
        LOGGER.info("Associated files will%s be preserved.", "" if preserve_files else " not")

        bib = Database()

        for label in labels:
            try:
                entry = bib[label]
                local_value = evaluate_as_f_string(value, {"label": label, **entry.data.copy()})

                if hasattr(entry, field):
                    prev_value = getattr(entry, field, None)
                else:
                    prev_value = entry.data.get(field, None)

                if not self.largs.add and not self.largs.remove:
                    new_value = local_value
                    if local_value.isnumeric():
                        new_value = int(local_value)  # type: ignore[assignment]
                elif self.largs.add:
                    try:
                        if prev_value is None:
                            new_value = local_value
                        elif isinstance(prev_value, str):
                            new_value = prev_value + local_value
                        elif isinstance(prev_value, list):
                            new_value = [*prev_value, local_value]  # type: ignore[assignment]
                        elif isinstance(prev_value, int):
                            if local_value.isnumeric():
                                new_value = prev_value + int(local_value)  # type: ignore[assignment]
                            else:
                                raise TypeError
                        else:
                            raise TypeError
                    except TypeError:
                        LOGGER.warning(
                            "Encountered an unexpected field type to add to. Converting the field "
                            "'%s' of entry '%s' to a simple string: '%s'.",
                            field,
                            label,
                            str(prev_value) + local_value,
                        )
                        new_value = str(prev_value) + local_value
                elif self.largs.remove:
                    try:
                        if isinstance(prev_value, list):
                            try:
                                new_value = copy(prev_value)  # type: ignore[assignment]
                                new_value.remove(local_value)  # type: ignore[attr-defined]
                            except ValueError:
                                LOGGER.warning(
                                    "Could not remove '%s' from the field '%s' of entry '%s'.",
                                    local_value,
                                    field,
                                    label,
                                )
                        elif isinstance(prev_value, int):
                            if local_value.isnumeric():
                                new_value = prev_value - int(local_value)  # type: ignore[assignment]
                            else:
                                raise TypeError
                        else:
                            raise TypeError
                    except TypeError:
                        LOGGER.warning(
                            "Encountered an unexpected field type to remove from. Leaving the field"
                            "'%s' of entry '%s' unchanged.",
                            field,
                            label,
                        )
                        new_value = prev_value  # type: ignore[assignment]

                # guard against overwriting existing data if label gets changed
                if field == "label":
                    new_value = bib.disambiguate_label(new_value, entry)

                if new_value == prev_value:
                    LOGGER.info(
                        "New and previous values match. Skipping modification of entry '%s'.", label
                    )
                    continue

                if hasattr(entry, field):
                    if self.largs.dry:
                        LOGGER.info(
                            "%s: changing field '%s' from %s to %s",
                            entry.label,
                            field,
                            getattr(entry, field),
                            new_value,
                        )
                    setattr(entry, field, new_value)
                else:
                    if self.largs.dry:
                        LOGGER.info(
                            "%s: adding field '%s' = %s",
                            entry.label,
                            field,
                            new_value,
                        )
                    entry.data[field] = new_value

                bib.update({entry.label: entry})

                if entry.label != label:
                    bib.rename(label, entry.label)
                    if not preserve_files:
                        new_files = []
                        for file in entry.file:
                            path = RelPath(file)
                            if path.path.stem == label:
                                LOGGER.info("Also renaming associated file '%s'.", str(path))
                                target = RelPath(path.path.parent / f"{entry.label}.pdf")
                                if target.path.exists():
                                    LOGGER.warning(
                                        "Found conflicting file, not renaming '%s'.", str(path)
                                    )
                                else:
                                    if self.largs.dry:
                                        LOGGER.info(
                                            "%s: renaming associated file '%s' to '%s'",
                                            entry.label,
                                            path.path,
                                            target.path,
                                        )
                                    else:
                                        path.path.rename(target.path)
                                        new_files.append(str(target))
                                    continue
                            if not self.largs.dry:
                                new_files.append(file)
                        if not self.largs.dry and new_files:
                            entry.file = new_files

                if not self.largs.dry:
                    self.modified_entries.append(entry)
                    msg = f"'{label}' was modified."
                    LOGGER.info(msg)
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                LOGGER.warning(msg)

        Event.PostModifyCommand.fire(self)

        if self.largs.dry:
            LOGGER.removeHandler(info_handler)
            # read also functions as a restoring method
            bib.read()
        else:
            bib.save()
            self.git()


def evaluate_ast_node(node: ast.expr, locals_: dict[str, Any] | None = None) -> str:
    """Evaluates an AST node representing an f-string.

    Args:
        node: the AST expression extracted from an f-string.
        locals_: the dictionary of local variables to be used as context for the expression
            evaluation. For convenience, this will include the `unidecode` method provided by
            [text-unidecode](https://pypi.org/project/text-unidecode).

    Returns:
        The evaluated AST node expression.
    """
    if locals_ is not None and "unidecode" not in locals_:
        locals_["unidecode"] = unidecode

    try:
        return eval(  # type: ignore
            compile(ast.Expression(node), filename="<string>", mode="eval"), locals_
        )
    except NameError as err:
        LOGGER.warning("You tried use an undefined variable. Falling back to an empty string.")
        LOGGER.error(err)
        return ""


def evaluate_as_f_string(value: str, locals_: dict[str, Any] | None = None) -> str:
    """Evaluates a string as if it were a literal f-string.

    Args:
        value: the string to be evaluated.
        locals_: the dictionary of local variables to be used as context for the expression
            evaluation. For convenience, this will include the `unidecode` method provided by
            [text-unidecode](https://pypi.org/project/text-unidecode).

    Returns:
        The evaluated f-string.

    Raises:
        ValueError: if an unexpected AST component type is encountered.

    References:
        <https://stackoverflow.com/a/61190684>
    """
    if locals_ is not None and "unidecode" not in locals_:
        locals_["unidecode"] = unidecode

    result: list[str] = []
    for part in ast.parse(f"f'''{value}'''").body[0].value.values:  # type: ignore
        typ = type(part)

        if typ is ast.Constant:
            result.append(part.value)

        elif typ is ast.FormattedValue:
            value = evaluate_ast_node(part.value, locals_)

            if part.conversion >= 0:
                conversions: dict[str, Callable[[Any], str]] = {"a": ascii, "r": repr, "s": str}
                value = conversions[chr(part.conversion)](value)

            if part.format_spec:
                value = format(value, evaluate_ast_node(part.format_spec, locals_))

            result.append(str(value))

        else:
            LOGGER.warning("Unexpected AST node expression type '%s' for an f-string.", typ)
            raise ValueError

    return "".join(result)
