r"""coBib's Modify command.

This command allows you to perform bulk modification to multiple entries.
Thus, it provides faster means to apply simple edits to many entries at once, without having to open
each entry for editing one-by-one or having to edit the database file manually.

A simple example is the following:
```
cobib modify tags:private --selection -- Label1 Label2 ...
```
which will set the tags of all listed entries to `private`.

You can use the `--add` option to not overwrite but append to existing values of a field. `str`
fields will be concatenated with*out* any spaces, lists will be appended, and numeric fields will be
added. Any other kind of field will be converted to a `str`.

As with other commands, you can also use filters (see also `cobib.commands.list`) rather than a
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

You can also trigger this command from the `cobib.tui.tui.TUI`.
By default, it is bound to the `m` key which will drop you into the prompt where you can type out a
normal command-line command:
```
:modify <arguments go here>
```

[^1]: <https://docs.python.org/3/reference/lexical_analysis.html#formatted-string-literals>
"""

from __future__ import annotations

import argparse
import ast
import logging
import os
import sys
from typing import IO, TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from cobib.config import Event
from cobib.database import Database
from cobib.utils.logging import get_stream_handler
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


def evaluate_ast_node(node: ast.expr, locals_: Optional[Dict[str, Any]] = None) -> str:
    """Evaluates an AST node representing an f-string.

    Args:
        node: the AST expression extracted from an f-string.
        locals_: the dictionary of local variables to be used as context for the expression
            evaluation.

    Returns:
        The evaluated AST node expression.
    """
    try:
        # pylint: disable=eval-used
        return eval(  # type: ignore
            compile(ast.Expression(node), filename="<string>", mode="eval"), locals_
        )
    except NameError as err:
        LOGGER.warning("You tried use an undefined variable. Falling back to an empty string.")
        LOGGER.error(err)
        return ""


def evaluate_as_f_string(value: str, locals_: Optional[Dict[str, Any]] = None) -> str:
    """Evaluates a string as if it were a literal f-string.

    Args:
        value: the string to be evaluated.
        locals_: the dictionary of local variables to be used as context for the expression
            evaluation.

    Returns:
        The evaluated f-string.

    Raises:
        ValueError: if an unexpected AST component type is encountered.

    References:
        <https://stackoverflow.com/a/61190684>
    """
    result: List[str] = []
    for part in ast.parse(f"f'''{value}'''").body[0].value.values:  # type: ignore
        typ = type(part)

        if typ is ast.Constant:
            result.append(part.value)

        elif typ is ast.Str:
            # TODO: remove once support for Python 3.7 will be dropped
            result.append(part.s)

        elif typ is ast.FormattedValue:
            value = evaluate_ast_node(part.value, locals_)

            if part.conversion >= 0:
                conversions: Dict[str, Callable[[Any], str]] = {"a": ascii, "r": repr, "s": str}
                value = conversions[chr(part.conversion)](value)

            if part.format_spec:
                value = format(value, evaluate_ast_node(part.format_spec))

            result.append(str(value))

        else:
            LOGGER.warning("Unexpected AST node expression type '%s' for an f-string.", typ)
            raise ValueError

    return "".join(result)


class ModifyCommand(Command):
    """The Modify Command."""

    name = "modify"

    @staticmethod
    def field_value_pair(string: str) -> Tuple[str, str]:
        """Utility method to assert the field-value pair argument type.

        This method is given to the `argparse.ArgumentParser` instance as its `type` specifier.
        An input argument is considered valid if it passes through this function without raising any
        errors, which means it conforms to the `<field>:<value>` notation.

        Args:
            string: the argument string to check.
        """
        # try splitting the string into field and value, any errors will be handled by argparse
        field, *value = string.split(":")
        # NOTE: we split only the first field off in case the value contains f-string format
        # specifications
        return (field, ":".join(value))

    # pylint: disable=too-many-branches,too-many-statements
    def execute(self, args: List[str], out: IO[Any] = sys.stdout) -> None:
        """Modifies multiple entries in bulk.

        This command allows bulk modification of multiple entries.
        It takes a modification in the form `<field>:<value>` and will overwrite the `field` of all
        matching entries with the new `value`.
        The entries can be specified as a manual selection (when using `--selection` or the visual
        selection of the TUI) or through filters (see also `cobib.commands.list`).

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `modification`: a string conforming to `<field>:<value>` indicating the
                      modification that should be applied to all matching entries. By default, the
                      modification will overwrite any existing data in the specified `field` with
                      the new `value`. For more information about formatting options of `<value>`
                      refer to the module documentation or the man-page.
                    * `--dry`: run in "dry"-mode which lists modifications without applying them.
                    * `-a`, `--add`: when specified, the modification's value will be added to the
                      entry's field rather than overwrite it. If the field in question is numeric,
                      the numbers will be added.
                    * `-s`, `--selection`: when specified, the positional arguments will *not* be
                      interpreted as filters but rather as a direct list of entry labels. This can
                      be used on the command-line but is mainly meant for the TUIs visual selection
                      interface (hence the name).
                    * in addition to the above, you can add `filters` to specify a subset of your
                      database for exporting. For more information refer to `cobib.commands.list`.
            out: the output IO stream. This defaults to `sys.stdout`.
        """
        LOGGER.debug("Starting Modify command.")
        parser = ArgumentParser(prog="modify", description="Modify subcommand parser.")
        parser.add_argument(
            "modification",
            type=self.field_value_pair,
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
        parser.add_argument(
            "-a",
            "--add",
            action="store_true",
            help="Adds to the modified field rather than overwriting it.",
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
        parser.add_argument(
            "--preserve-files", action="store_true", help="do not rename associated files"
        )

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            LOGGER.error(exc.message)
            return

        Event.PreModifyCommand.fire(largs)

        info_handler: logging.Handler
        if largs.dry:
            info_handler = get_stream_handler(logging.INFO)

            class ModifyInfoFilter(logging.Filter):
                """A logging filter to only print ModifyCommand INFO messages."""

                def filter(self, record: logging.LogRecord) -> bool:
                    return record.name == "cobib.commands.modify" and record.levelname == "INFO"

            info_handler.addFilter(ModifyInfoFilter())
            LOGGER.addHandler(info_handler)

        if largs.selection:
            LOGGER.info("Selection given. Interpreting `filter` as a list of labels")
            labels = largs.filter
        else:
            LOGGER.debug("Gathering filtered list of entries to be modified.")
            with open(os.devnull, "w", encoding="utf-8") as devnull:
                labels = ListCommand().execute(largs.filter, out=devnull)

        field, value = largs.modification

        bib = Database()

        for label in labels:  # pylint: disable=too-many-nested-blocks
            try:
                entry = bib[label]
                local_value = evaluate_as_f_string(value, {"label": label, **entry.data.copy()})

                if hasattr(entry, field):
                    prev_value = getattr(entry, field, None)
                else:
                    prev_value = entry.data.get(field, None)

                if not largs.add:
                    new_value = local_value
                    if local_value.isnumeric():
                        new_value = int(local_value)  # type: ignore
                else:
                    try:
                        if prev_value is None:
                            new_value = local_value
                        elif isinstance(prev_value, str):
                            new_value = prev_value + local_value
                        elif isinstance(prev_value, list):
                            new_value = prev_value + [local_value]  # type: ignore
                        elif isinstance(prev_value, int):
                            if local_value.isnumeric():
                                new_value = prev_value + int(local_value)  # type: ignore
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

                # guard against overwriting existing data if label gets changed
                if field == "label":
                    new_value = bib.disambiguate_label(new_value)

                if new_value == prev_value:
                    LOGGER.info(
                        "New and previous values match. Skipping modification of entry '%s'.", label
                    )
                    continue

                if hasattr(entry, field):
                    if largs.dry:
                        LOGGER.info(
                            "%s: changing field '%s' from %s to %s",
                            entry.label,
                            field,
                            getattr(entry, field),
                            new_value,
                        )
                    setattr(entry, field, new_value)
                else:
                    if largs.dry:
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
                    if not largs.preserve_files:
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
                                    if largs.dry:
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
                            if not largs.dry:
                                new_files.append(file)
                        if not largs.dry:
                            entry.file = new_files

                if not largs.dry:
                    msg = f"'{label}' was modified."
                    LOGGER.info(msg)
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                LOGGER.warning(msg)

        Event.PostModifyCommand.fire(labels, largs.dry)

        if largs.dry:
            LOGGER.removeHandler(info_handler)
            # read also functions as a restoring method
            bib.read()
        else:
            bib.save()
            self.git(args=vars(largs))

    @staticmethod
    def tui(tui: cobib.tui.TUI) -> None:
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.debug("Modify command triggered from TUI.")
        # handle input via prompt
        if tui.selection:
            tui.execute_command("modify -s", pass_selection=True)
        else:
            tui.execute_command("modify")
