"""coBib command-line test class."""

from __future__ import annotations

import runpy
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pytest


class CmdLineTest:
    """A command-line test runs coBib's command-line interface."""

    @staticmethod
    def run_module(monkeypatch: pytest.MonkeyPatch, main: str, sys_argv: List[str]) -> None:
        """Gets the coBib runtime module after monkeypatching sys.argv."""
        monkeypatch.setattr("sys.argv", sys_argv)
        module = runpy.run_module("cobib")  # type: ignore
        module.get(main)()