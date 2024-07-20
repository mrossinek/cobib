"""Tests for coBib's Event validation."""

from __future__ import annotations

from collections.abc import Generator
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
