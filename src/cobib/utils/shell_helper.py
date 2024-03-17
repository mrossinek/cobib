"""coBib's shell helpers.

This module provides a variety of shell helper utilities.

This entire module is deprecated and will be removed in version 5.0 of coBib.
"""

from __future__ import annotations

import argparse
import contextlib
import inspect
import logging
from io import StringIO

from rich.console import Console
from rich.prompt import PromptBase, PromptType
from textual.app import App

from .rel_path import RelPath

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


def list_commands(*args: str) -> list[str]:
    """Lists all available subcommands.

    Args:
        args: a sequence of additional arguments used for the execution. None are supported yet.

    Returns:
        The list of available commands.
    """
    msg = "The _list_commands shell helper utility is deprecated and will be removed in the future!"
    LOGGER.warning(msg)

    from cobib import commands

    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_labels(*args: str) -> list[str]:
    """List all available labels in the database.

    Args:
        args: a sequence of additional arguments used for the execution. None are supported yet.

    Returns:
        The list of all labels.
    """
    msg = "The _list_labels shell helper utility is deprecated and will be removed in the future!"
    LOGGER.warning(msg)

    from cobib.database import Database

    labels = list(Database().keys())
    return labels


def list_filters(*args: str) -> set[str]:
    """Lists all field names available for filtering.

    Args:
        args: a sequence of additional arguments used for the execution. None are supported yet.

    Returns:
        The list of all available filters.
    """
    msg = "The _list_filters shell helper utility is deprecated and will be removed in the future!"
    LOGGER.warning(msg)

    from cobib.database import Database

    filters: set[str] = {"label"}
    for entry in Database().values():
        filters.update(entry.data.keys())
    return filters


def example_config(*args: str) -> list[str]:
    """Shows the (well-commented) example configuration.

    Args:
        args: a sequence of additional arguments used for the execution. None are supported yet.

    Returns:
        The lines of the example config file.
    """
    msg = (
        "The '_example_config' shell helper utility will be refactored to become the "
        "'example_config' command in version 5.0 of coBib."
    )
    LOGGER.warning(msg)

    root = RelPath(__file__).parent.parent
    with open(root / "config/example.py", "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines()]


class LintFormatter(logging.Formatter):
    """A custom logging.Formatter."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Initializes a LintFormatter."""
        super().__init__(*args, **kwargs)

        self.dirty_entries: set[str] = set()

        from cobib.config import config

        self._database_path = RelPath(config.database.file)

        with open(self._database_path.path, "r", encoding="utf-8") as database:
            self._raw_database = database.readlines()

    def format(self, record: logging.LogRecord) -> str:
        """Format's the LogRecord.

        This custom Formatter uses the LogRecord's attributes to determine from which line of the
        raw database a formatting information was raised. The corresponding line number is used in
        conjunction with the actual message of the LogRecord for the formatting.

        Args:
            record: the LogRecord to be formatted.

        Returns:
            A string encoding the LogRecord's information.
        """
        try:
            entry = record.entry  # type: ignore[attr-defined]
            field = record.field  # type: ignore[attr-defined]
            self.dirty_entries.add(entry)
            raw_db = enumerate(self._raw_database)
            _, line = next(raw_db)
            while not line.startswith(entry):
                _, line = next(raw_db)
            while not line.strip().startswith(field):
                line_no, line = next(raw_db)
            return f"{self._database_path}:{line_no+1} {record.getMessage()}"
        except AttributeError:
            return ""


def lint_database(*args: str) -> list[str]:
    """Lints the users database.

    Args:
        args: a sequence of additional arguments used for the execution. Currently, only a single
            optional value is allowed:
                * `-f`, `--format`: if specified, the database will be formatted to automatically
                    resolve all lint messages.

    Returns:
        The list of INFO log messages raised upon Entry initialization.
    """
    msg = (
        "The '_lint_database' shell helper utility will be refactored to become the 'lint' command "
        "in version 5.0 of coBib."
    )
    LOGGER.warning(msg)

    parser = argparse.ArgumentParser(prog="lint_database", description="A database format linter.")
    parser.add_argument(
        "-f",
        "--format",
        action="store_true",
        help="Automatically format database to conform with linter.",
    )
    largs = parser.parse_args(args)

    from cobib.database import Database

    output = StringIO()

    handler = logging.StreamHandler(output)
    handler.setLevel(logging.INFO)
    handler.addFilter(logging.Filter("cobib.database.entry"))

    formatter = LintFormatter()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if root_logger.getEffectiveLevel() > logging.INFO:
        # overwriting all existing handlers with this local one
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.INFO)
    else:
        # appending new handler
        root_logger.addHandler(handler)

    # trigger database reading to cause lint messages upon entry-construction
    Database.read(bypass_cache=True)

    lint_messages = output.getvalue().split("\n")

    root_logger.removeHandler(handler)

    if all(not msg for msg in lint_messages):
        return ["Congratulations! Your database triggers no lint messages."]

    if largs.format:
        for label in formatter.dirty_entries:
            # we exploit the rename method to register all dirty entries for re-writing
            Database().rename(label, label)

        Database.save()

        from cobib.commands.base_command import Command

        # generate automatic git commit
        class LintCommand(Command):
            """The linting command."""

            name = "lint"

            def __init__(
                self,
                *args: str,
                console: Console | App[None] | None = None,
                prompt: type[PromptBase[PromptType]] | None = None,
            ) -> None:
                self.largs = largs

            @classmethod
            def init_argparser(cls) -> None:
                pass

            def execute(self):  # type: ignore
                pass

        LintCommand().git()

        return ["The following lint messages have successfully been resolved:", *lint_messages]

    return lint_messages


def unify_labels(*args: str) -> list[str]:
    """Unifies all labels of the database according to `config.database.format.label_default`.

    Without the `--apply` argument this will only print the modification which would be performed!

    Args:
        args: a sequence of additional arguments used for the execution. Currently, only a single
            optional value is allowed:
                * `-a`, `--apply`: if specified, the label unification will actually be applied. The
                    default is to run in "dry"-mode which only prints the modifications.

    Returns:
        The list of INFO log messages raised upon label unification.
    """
    msg = (
        "The '_unify_labels' shell helper utility will be refactored to become the 'unify_labels' "
        "command in version 5.0 of coBib."
    )
    LOGGER.warning(msg)

    parser = argparse.ArgumentParser(prog="unify_labels", description="Label unification")
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="Actually apply the modifications rather than run in 'dry'-mode",
    )
    largs = parser.parse_args(args)

    from cobib.commands import ModifyCommand
    from cobib.config import config

    modify_args = [
        "--dry",
        f"label:{config.database.format.label_default}",
        "--",
        "--label",
        "some_non_existent_label",  # this ensures that the command gets run on the entire database
    ]
    if largs.apply:
        modify_args = modify_args[1:]

    with contextlib.redirect_stderr(StringIO()) as out:
        cmd = ModifyCommand(*modify_args)
        cmd.execute()

    return out.getvalue().strip().split("\n")
