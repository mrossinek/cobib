"""A dummy command."""

from __future__ import annotations

import argparse

from typing_extensions import override

from cobib.commands.base_command import Command


class DummyCommand(Command):
    """A dummy command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="dummy", description="Dummy subcommand parser.", exit_on_error=True
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        print("DummyCommand.execute")
