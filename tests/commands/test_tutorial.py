"""Tests for coBib's TutorialCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import TutorialCommand

from .command_test import CommandTest

if TYPE_CHECKING:
    import cobib.commands


class TestTutorialCommand(CommandTest):
    """Tests for coBib's TutorialCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return TutorialCommand

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_stdin", [{"stdin_list": ["quit\n"]}], indirect=["mock_stdin"])
    async def test_command(self, mock_stdin: Any) -> None:
        """Test the command itself.

        Args:
            mock_stdin: an additional setup fixture.
        """
        cmd = TutorialCommand()
        await cmd.execute()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_stdin", [{"stdin_list": ["quit\n"]}], indirect=["mock_stdin"])
    async def test_cmdline(self, mock_stdin: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            mock_stdin: an additional setup fixture.
            monkeypatch: the built-in pytest fixture.
        """
        await self.run_module(monkeypatch, "main", ["cobib", "tutorial"])
