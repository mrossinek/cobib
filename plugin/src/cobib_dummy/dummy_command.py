"""A dummy command."""

from __future__ import annotations

from typing_extensions import override

from cobib.commands.base_command import ArgumentParser, Command


class DummyCommand(Command):
    """A dummy command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="dummy", description="Dummy subcommand parser.")
        cls.argparser = parser

    @override
    def execute(self) -> None:
        print("DummyCommand.execute")
