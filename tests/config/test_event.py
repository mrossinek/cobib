"""Tests for coBib's Event validation."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from cobib.config import Event, config

from .. import get_resource


@pytest.fixture(autouse=True)
def setup() -> Generator[Any, None, None]:
    """Setup debugging configuration.

    Yields:
        Access to the local fixture variables.
    """
    config.load(get_resource("debug.py"))
    yield setup
    config.defaults()


@pytest.mark.parametrize("event", list(Event))
def test_config_validation(event: Event) -> None:
    """Test the config validation of faulty hook subscription functions.

    Args:
        event: the coBib Event which to subscribe to.
    """

    @event.subscribe
    def faulty_hook() -> None:
        return

    with pytest.raises(RuntimeError) as exc_info:
        config.validate()

    assert (
        str(exc_info.value)
        == f"config.events.Event.{event.name} did not pass its validation check."
    )


def test_multiple_event_hooks(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the execution of multiple event hooks.

    Args:
        capsys: the built-in pytest fixture.
    """

    @Event.PostGitCommit.subscribe
    def hook1(root: Path, file: Path) -> None:
        print(f"root={root}")

    @Event.PostGitCommit.subscribe
    def hook2(root: Path, file: Path) -> None:
        print(f"file={file}")

    a = Path("./a")
    b = Path("./b")
    Event.PostGitCommit.fire(a, b)

    assert capsys.readouterr().out.strip() == "root=a\nfile=b"
