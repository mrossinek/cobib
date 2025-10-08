"""General tests for the Shell."""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any, Optional

import pytest

from cobib.config import Event, config
from cobib.database import Database
from cobib.ui import Shell
from cobib.utils.console import PromptConsole

from ... import get_resource
from ...cmdline_test import CmdLineTest

# FIXME: this is still not 100% predictable, but at least it seems to work reliably inside of tox/CI
FORCE_TERMINAL = os.getenv("TOX_ENV_NAME", default="") == ""


class TestShellGeneral(CmdLineTest):
    """General tests for the Shell."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        config.load(get_resource("debug.py"))
        PromptConsole.clear_instance()
        yield
        Database.read()
        config.defaults()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_stdin", [{"stdin_list": ["quit\n"]}], indirect=["mock_stdin"])
    async def test_cmdline(
        self, mock_stdin: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the shell.

        Args:
            mock_stdin: an additional setup fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            await super().run_module(monkeypatch, "main", ["cobib", "-p", "-s"])
        out = capsys.readouterr().out
        expected = "The --porcelain mode has no effect on an interactive UI!".split()
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mock_stdin", [{"stdin_list": ["help\n", "exit\n"]}], indirect=["mock_stdin"]
    )
    async def test_help(self, mock_stdin: Any, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the `help` alias of the interactive shell.

        Args:
            mock_stdin: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        expected = "a simple interactive shell can suffice".split()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mock_stdin", [{"stdin_list": ["git --help\n", "exit\n"]}], indirect=["mock_stdin"]
    )
    async def test_help_command(self, mock_stdin: Any, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the requesting `--help` for a command does not exit the interactive shell.

        Args:
            mock_stdin: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        expected = "Read cobib-git.1 and cobib-git.7 for more help.".split()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mock_stdin", [{"stdin_list": ["asdf\n", "exit\n"]}], indirect=["mock_stdin"]
    )
    async def test_catch_unknown_command(
        self, mock_stdin: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the graceful handling of an unknown command during the interactive shell.

        Args:
            mock_stdin: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        expected = "Encountered an unknown command: 'asdf'!".split()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["expected", "mock_stdin"],
        [
            (
                "Congratulations! Your database triggers no lint messages.".split(),
                # NOTE: this tests a synchronous command execution
                {"stdin_list": ["lint\n", "exit\n"]},
            ),
            (
                "The entry 'einstein' has no actionable field associated with it.".split(),
                # NOTE: this tests an asynchronous command execution
                {"stdin_list": ["open einstein\n", "exit\n"]},
            ),
        ],
        indirect=["mock_stdin"],
    )
    async def test_command(
        self, expected: list[str], mock_stdin: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the execution of "standard" commands.

        Args:
            expected: the expected string for which to check in captured stdout.
            mock_stdin: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_stdin", [{"stdin_list": ["exit\n"]}], indirect=["mock_stdin"])
    async def test_event_pre_shell_input(
        self, mock_stdin: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the PreShellInput event.

        Args:
            mock_stdin: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        greeting = "Hello, world!"

        @Event.PreShellInput.subscribe
        def hook(shell: Shell) -> None:
            shell.live.console.print(greeting)

        assert Event.PreShellInput.validate()

        await Shell().run_async()

        out = capsys.readouterr().out
        for word in greeting.split():
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_stdin", [{"stdin_list": ["asdf\n"]}], indirect=["mock_stdin"])
    async def test_event_post_shell_input(self, mock_stdin: Any) -> None:
        """Tests the PostShellInput event.

        Args:
            mock_stdin: an additional setup fixture.
        """

        @Event.PostShellInput.subscribe
        def hook(text: str) -> Optional[str]:
            return "quit"

        assert Event.PostShellInput.validate()

        await Shell().run_async()
