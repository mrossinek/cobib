"""coBib's command-line test class."""

from __future__ import annotations

import os
import runpy
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pytest


class CmdLineTest:
    """A command-line test runs coBib's command-line interface."""

    @staticmethod
    async def run_module(monkeypatch: pytest.MonkeyPatch, main: str, sys_argv: List[str]) -> None:
        """Gets the coBib runtime module after monkeypatching `sys.argv`.

        Args:
            monkeypatch: the built-in pytest fixture.
            main: the name of the `main` executable of the module to run.
            sys_argv: the list of values with which to monkeypatch `sys.argv`.
        """
        os.environ["COBIB_CONFIG"] = "0"
        monkeypatch.setattr("sys.argv", sys_argv)
        module = runpy.run_module("cobib")
        await module.get(main)()  # type: ignore
