"""coBib's command-line test class."""

from __future__ import annotations

import os
import runpy
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

from cobib.utils.console import HAS_OPTIONAL_PROMPT_TOOLKIT

if HAS_OPTIONAL_PROMPT_TOOLKIT:
    from prompt_toolkit.application import create_app_session
    from prompt_toolkit.input import PipeInput, create_pipe_input
    from prompt_toolkit.output import DummyOutput
else:
    from . import MockStdin

if TYPE_CHECKING:
    import _pytest.fixtures


class CmdLineTest:
    """A command-line test runs coBib's command-line interface."""

    @staticmethod
    async def run_module(monkeypatch: pytest.MonkeyPatch, main: str, sys_argv: list[str]) -> None:
        """Gets the coBib runtime module after monkeypatching `sys.argv`.

        Args:
            monkeypatch: the built-in pytest fixture.
            main: the name of the `main` executable of the module to run.
            sys_argv: the list of values with which to monkeypatch `sys.argv`.
        """
        os.environ["COBIB_CONFIG"] = "0"
        monkeypatch.setattr("sys.argv", sys_argv)
        module = runpy.run_module("cobib")
        await module.get(main)()  # type: ignore[misc]

    @pytest.fixture
    def mock_stdin(
        self, monkeypatch: pytest.MonkeyPatch, request: _pytest.fixtures.SubRequest
    ) -> Generator[PipeInput, None, None]:
        """A fixture to mock `sys.stdin`, handling the optional presence of `prompt_toolkit`.

        Args:
            monkeypatch: the built-in pytest fixture.
            request: a pytest sub-request providing access to nested parameters.

        Yields:
            The internally used parameters for potential later re-use during the actual test.
        """
        if not hasattr(request, "param"):
            # use default settings
            request.param = {"stdin_list": []}

        if HAS_OPTIONAL_PROMPT_TOOLKIT:
            with create_pipe_input() as pipe_input:
                with create_app_session(input=pipe_input, output=DummyOutput()):
                    for line in request.param["stdin_list"]:
                        pipe_input.send_text(line)
                    yield pipe_input
        else:
            monkeypatch.setattr("sys.stdin", MockStdin(request.param.get("stdin_list", None)))
            yield request.param
