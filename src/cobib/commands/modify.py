r"""Modify entries in bulk.

.. include:: ../man/cobib-modify.1.html_fragment
"""

from __future__ import annotations

import argparse
import ast
import logging
from collections.abc import Callable
from copy import copy
from io import StringIO
from typing import Any, cast

from rich.console import ConsoleRenderable
from rich.text import Text
from text_unidecode import unidecode
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.utils.logging import get_stream_handler
from cobib.utils.rel_path import RelPath

from .base_command import Command
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
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.modified_entries: list[Entry] = []
        """A list of `cobib.database.Entry` objects which were modified by this command.

        This is **not** populated when the `--dry` mode is used.
        """

        self.modification_details: list[str] = []
        """A list of captured log messages, detailing the applied modifications.

        This is **only** populated when the `--dry` mode is used.
        """

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
        parser = argparse.ArgumentParser(
            prog="modify",
            description="Modify subcommand parser.",
            epilog="Read cobib-modify.1 for more help.",
        )
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

        info_handler: logging.StreamHandler[StringIO]
        if self.largs.dry:
            info_handler = get_stream_handler(logging.INFO)

            class ModifyInfoFilter(logging.Filter):
                """A logging filter to only print ModifyCommand INFO messages."""

                def filter(self, record: logging.LogRecord) -> bool:
                    return record.name == "cobib.commands.modify" and record.levelname == "INFO"

            LOGGER.debug("Starting to capture modification logging messages")
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

                if not local_value:
                    if field == "label":
                        LOGGER.error("The `label` field may not be empty and cannot be removed!")
                        return

                    if not self.largs.remove:
                        LOGGER.warning(
                            "You have specified an empty modification value without the `--remove` "
                            "flag! This will only overwrite the field with an empty value, if you "
                            "wish to also delete it, you must add that flag."
                        )

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
                            raise TypeError  # pragma: no cover
                    except TypeError:
                        LOGGER.warning(
                            "Encountered an unexpected field type to add to. Converting the field "
                            "'%s' of entry '%s' to a simple string: '%s'.",
                            field,
                            label,
                            str(prev_value) + local_value,
                        )
                        new_value = str(prev_value) + local_value
                elif self.largs.remove:  # pragma: no branch
                    try:
                        if not local_value:
                            LOGGER.info(
                                "An empty modification value was provided together with the "
                                "`--remove` flag. Removing the entire field."
                            )
                            new_value = None
                        elif isinstance(prev_value, list):
                            try:
                                new_value = copy(prev_value)  # type: ignore[assignment]
                                new_value.remove(local_value)  # type: ignore[union-attr]
                            except ValueError:  # pragma: no cover
                                LOGGER.warning(  # pragma: no cover
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
                        new_value = prev_value

                # guard against overwriting existing data if label gets changed
                if field == "label":
                    new_value = bib.disambiguate_label(cast(str, new_value), entry)

                if new_value == prev_value:
                    LOGGER.info(
                        "New and previous values match. Skipping modification of entry '%s'.", label
                    )
                    continue

                if new_value is None:
                    if self.largs.dry:
                        LOGGER.info(  # pragma: no cover
                            "%s: removing the field '%s'", entry.label, field
                        )
                    entry.data.pop(field)
                elif hasattr(entry, field):
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
                        LOGGER.info(  # pragma: no cover
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
                                    LOGGER.warning(  # pragma: no cover
                                        "Found conflicting file, not renaming '%s'.", str(path)
                                    )
                                else:
                                    if self.largs.dry:
                                        LOGGER.info(  # pragma: no cover
                                            "%s: renaming associated file '%s' to '%s'",
                                            entry.label,
                                            path.path,
                                            target.path,
                                        )
                                    else:
                                        path.path.rename(target.path)
                                        new_files.append(str(target))
                                    continue
                            if not self.largs.dry:  # pragma: no cover
                                new_files.append(file)  # pragma: no cover
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

            messages = info_handler.stream.getvalue()
            self.modification_details = [msg for msg in messages.split("\n") if msg]
        else:
            bib.save()
            self.git()

    @override
    def render_porcelain(self) -> list[str]:
        return self.modification_details

    @override
    def render_rich(self) -> ConsoleRenderable:
        text = Text("\n".join(self.modification_details))  # pragma: no cover
        text.highlight_words(["ERROR"], "bold red")  # pragma: no cover
        text.highlight_words(["WARNING"], "bold yellow")  # pragma: no cover
        text.highlight_words(["HINT"], "green")  # pragma: no cover
        text.highlight_words(["INFO"], "blue")  # pragma: no cover
        return text  # pragma: no cover


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
        locals_["unidecode"] = unidecode  # pragma: no cover

    try:
        return eval(  # type: ignore[no-any-return]
            compile(ast.Expression(node), filename="<string>", mode="eval"), locals_
        )
    except NameError as err:
        LOGGER.warning("You tried to use an undefined variable. Falling back to an empty string.")
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
    if locals_ is not None and "unidecode" not in locals_:  # pragma: no branch
        locals_["unidecode"] = unidecode

    result: list[str] = []
    for part in ast.parse(f"f'''{value}'''").body[0].value.values:  # type: ignore[attr-defined]
        type_ = type(part)

        if type_ is ast.Constant:
            result.append(part.value)

        elif type_ is ast.FormattedValue:
            value = evaluate_ast_node(part.value, locals_)

            if part.conversion >= 0:
                conversions: dict[str, Callable[[Any], str]] = {"a": ascii, "r": repr, "s": str}
                value = conversions[chr(part.conversion)](value)

            if part.format_spec:
                value = format(value, evaluate_ast_node(part.format_spec, locals_))

            result.append(str(value))

        else:
            LOGGER.warning(  # pragma: no cover
                "Unexpected AST node expression type '%s' for an f-string.", type_
            )
            raise ValueError  # pragma: no cover

    return "".join(result)
