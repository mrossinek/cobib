"""Tests for coBib's TUI state."""
# pylint: disable=redefined-outer-name

import copy

import pytest

from cobib.config import config
from cobib.tui.state import STATE, Mode, State

from .. import get_resource


@pytest.fixture
def setup() -> None:
    """Setup."""
    config.load(get_resource("debug.py"))


def test_state_reset() -> None:
    """Test `cobib.tui.state.State.reset`."""
    state = copy.deepcopy(STATE)
    state.top_line = 10
    assert state.top_line == 10
    state.reset()
    assert state.top_line == 0


@pytest.mark.parametrize(
    ["reverse_order"],
    [
        [False],
        [True],
    ],
)
def test_state_initialize(reverse_order: bool) -> None:
    """Test config-dependent state-initialization.

    Args:
        reverse_order: whether to add the `--reverse` flag to the `default_list_args`.
    """
    config.tui.reverse_order = reverse_order
    state = copy.deepcopy(STATE)
    state.initialize()
    try:
        assert state.top_line == 0
        assert state.left_edge == 0
        assert state.current_line == 0
        assert state.previous_line == -1

        assert state.mode == Mode.LIST.value
        assert state.inactive_commands == []
        assert state.topstatus == ""

        state.list_args = config.tui.default_list_args
        if config.tui.reverse_order:
            state.list_args += ["-r"]
    finally:
        config.defaults()


def test_state_update() -> None:
    """Test `cobib.tui.state.State.update`."""
    state = copy.deepcopy(STATE)
    dummy_state = State()
    dummy_state.top_line = "dummy"  # type: ignore
    dummy_state.left_edge = "dummy"  # type: ignore
    dummy_state.current_line = "dummy"  # type: ignore
    dummy_state.previous_line = "dummy"  # type: ignore
    dummy_state.mode = "dummy"
    dummy_state.inactive_commands = "dummy"  # type: ignore
    dummy_state.topstatus = "dummy"
    dummy_state.list_args = "dummy"  # type: ignore

    state.update(dummy_state)
    assert dummy_state.top_line == "dummy"  # type: ignore
    assert dummy_state.left_edge == "dummy"  # type: ignore
    assert dummy_state.current_line == "dummy"  # type: ignore
    assert dummy_state.previous_line == "dummy"  # type: ignore
    assert dummy_state.mode == "dummy"
    assert dummy_state.inactive_commands == "dummy"  # type: ignore
    assert dummy_state.topstatus == "dummy"
    assert dummy_state.list_args == "dummy"  # type: ignore
