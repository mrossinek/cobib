"""coBib's example configuration command.

This command can be used to extract the default (or example) configuration for the installed coBib
version.

You can run this command via:
```
cobib _example_config
```
"""

from __future__ import annotations

import argparse

from rich.console import ConsoleRenderable
from rich.syntax import Syntax
from typing_extensions import override

from cobib.commands.base_command import Command
from cobib.utils.rel_path import RelPath


class ExampleConfigCommand(Command):
    """The example configuration Command.

    This command does not take any arguments.
    """

    name = "example_config"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self._contents: list[str] = []

    @override
    @classmethod
    def init_argparser(cls) -> None:
        cls.argparser = argparse.ArgumentParser(prog="example_config", exit_on_error=True)

    @override
    def execute(self) -> None:
        root = RelPath(__file__).parent.parent
        with open(root / "config/example.py", "r", encoding="utf-8") as file:
            self._contents = [line.strip() for line in file.readlines()]

    @override
    def render_porcelain(self) -> list[str]:
        return self._contents

    @override
    def render_rich(self, *, background_color: str = "default") -> ConsoleRenderable:
        syntax = Syntax(
            "\n".join(self._contents), "python", background_color=background_color, word_wrap=False
        )
        return syntax
