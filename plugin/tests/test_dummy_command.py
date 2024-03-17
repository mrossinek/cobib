"""Tests for the dummy command."""

from __future__ import annotations

import pytest

from . import run_module


class TestDummyCommand:
    """Tests for the dummy command."""

    @pytest.mark.asyncio
    async def test_cmdline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test the command-line access of the command.

        Args:
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        await run_module(monkeypatch, "main", ["cobib", "-p", "dummy"])

        assert capsys.readouterr().out.strip() == "DummyCommand.execute"
