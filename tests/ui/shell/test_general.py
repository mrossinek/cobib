"""General tests for the Shell."""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Optional

import pytest

from cobib.config import Event, config
from cobib.database import Database
from cobib.ui import Shell
from cobib.ui.components.console import HAS_OPTIONAL_PROMPT_TOOLKIT

if HAS_OPTIONAL_PROMPT_TOOLKIT:
    from prompt_toolkit.application import create_app_session
    from prompt_toolkit.input import PipeInput, create_pipe_input
    from prompt_toolkit.output import DummyOutput
else:
    from ... import MockStdin

from ... import CmdLineTest, get_resource

if TYPE_CHECKING:
    import _pytest.fixtures


# FIXME: this is still not 100% predictable, but at least it seems to work reliably inside of tox/CI
FORCE_TERMINAL = os.environ.get("TOX_ENV_NAME", "") == ""


class TestShellGeneral(CmdLineTest):
    """General tests for the Shell."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Load testing config."""
        config.load(get_resource("debug.py"))
        yield
        Database.read()
        config.defaults()

    @pytest.fixture
    def post_setup(
        self, monkeypatch: pytest.MonkeyPatch, request: _pytest.fixtures.SubRequest
    ) -> Generator[PipeInput, None, None]:
        """Additional setup instructions.

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

    @pytest.mark.asyncio
    @pytest.mark.parametrize("post_setup", [{"stdin_list": ["quit\n"]}], indirect=["post_setup"])
    async def test_cmdline(
        self, post_setup: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the shell.

        Args:
            post_setup: an additional setup fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        with pytest.raises(SystemExit):
            await super().run_module(monkeypatch, "main", ["cobib", "-p", "-s"])
        outerr = capsys.readouterr()
        assert "The --porcelain mode has no effect on an interactive UI!" in outerr.err

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "post_setup", [{"stdin_list": ["help\n", "exit\n"]}], indirect=["post_setup"]
    )
    async def test_help(self, post_setup: Any, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the `help` alias of the interactive shell.

        Args:
            post_setup: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        expected = "a simple interactive shell can suffice".split()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "post_setup", [{"stdin_list": ["git --help\n", "exit\n"]}], indirect=["post_setup"]
    )
    async def test_help_command(self, post_setup: Any, capsys: pytest.CaptureFixture[str]) -> None:
        """Tests the requesting `--help` for a command does not exit the interactive shell.

        Args:
            post_setup: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        expected = "Read cobib-git.1 and cobib-git.7 for more help.".split()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "post_setup", [{"stdin_list": ["asdf\n", "exit\n"]}], indirect=["post_setup"]
    )
    async def test_catch_unknown_command(
        self, post_setup: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the graceful handling of an unknown command during the interactive shell.

        Args:
            post_setup: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        expected = "Encountered an unknown command: 'asdf'!".split()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["expected", "post_setup"],
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
        indirect=["post_setup"],
    )
    async def test_command(
        self, expected: list[str], post_setup: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the execution of "standard" commands.

        Args:
            expected: the expected string for which to check in captured stdout.
            post_setup: an additional setup fixture.
            capsys: the built-in pytest fixture.
        """
        await Shell().run_async()
        out = capsys.readouterr().out
        for word in expected:
            assert word in out

    @pytest.mark.asyncio
    @pytest.mark.parametrize("post_setup", [{"stdin_list": ["exit\n"]}], indirect=["post_setup"])
    async def test_event_pre_shell_input(
        self, post_setup: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the PreShellInput event.

        Args:
            post_setup: an additional setup fixture.
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
    @pytest.mark.parametrize("post_setup", [{"stdin_list": ["asdf\n"]}], indirect=["post_setup"])
    async def test_event_post_shell_input(self, post_setup: Any) -> None:
        """Tests the PostShellInput event.

        Args:
            post_setup: an additional setup fixture.
        """

        @Event.PostShellInput.subscribe
        def hook(text: str) -> Optional[str]:
            return "quit"

        assert Event.PostShellInput.validate()

        await Shell().run_async()
