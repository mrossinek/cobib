"""Unify the entry labels.

.. include:: ../man/cobib-unify-labels.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from rich.console import ConsoleRenderable
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

        self._cmd: ModifyCommand

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="unify_labels",
            description="Label unification subcommand parser.",
            epilog="Read cobib-unify-labels.1 for more help.",
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

        self._cmd = ModifyCommand(*modify_args)
        self._cmd.execute()

    @override
    def render_porcelain(self) -> list[str]:
        return self._cmd.render_porcelain()

    @override
    def render_rich(self) -> ConsoleRenderable:
        return self._cmd.render_rich()
