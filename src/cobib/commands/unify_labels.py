"""Unify the entry labels.

.. include:: ../man/cobib-unify-labels.1.html_fragment
"""

from __future__ import annotations

import argparse
import contextlib
import logging
from io import StringIO

from rich.console import ConsoleRenderable
from rich.text import Text
from typing_extensions import override

from cobib.config import config

from .base_command import Command
from .modify import ModifyCommand

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class UnifyLabelsCommand(Command):
    """The label unification Command.

    This command can parse the following arguments:

        * `-a`, `--apply`: if specified, the label unification will actually be applied. The default
            is to run in "dry"-mode which only prints the modifications.
    """

    name = "unify_labels"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self._contents: list[str] = []

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="unify_labels",
            description="Label unification subcommand parser.",
            exit_on_error=True,
        )
        parser.add_argument(
            "-a",
            "--apply",
            action="store_true",
            help="Actually apply the modifications rather than run in 'dry'-mode",
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        modify_args = [
            f"label:{config.database.format.label_default}",
            "--",
            # the following ensures that the command gets run on the entire database
            "++label",
            "",
        ]
        if not self.largs.apply:
            modify_args.insert(0, "--dry")

        with contextlib.redirect_stderr(StringIO()) as out:
            cmd = ModifyCommand(*modify_args)
            cmd.execute()

        self._contents = out.getvalue().strip().split("\n")

    @override
    def render_porcelain(self) -> list[str]:
        return self._contents

    @override
    def render_rich(self) -> ConsoleRenderable:
        text = Text("\n".join(self._contents))  # pragma: no cover
        text.highlight_words(["ERROR"], "bold red")  # pragma: no cover
        text.highlight_words(["WARNING"], "bold yellow")  # pragma: no cover
        text.highlight_words(["HINT"], "green")  # pragma: no cover
        text.highlight_words(["INFO"], "blue")  # pragma: no cover
        return text  # pragma: no cover
