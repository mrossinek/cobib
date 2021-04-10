"""coBib's TUI State object.

This object gathers all the stateful information of the TUI.
It provides utility methods to `reset` the State to it's starting point and an `update` method to
set the State to a previously stored version.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import List

from cobib.config import config

LOGGER = logging.getLogger(__name__)


class Mode(Enum):
    """An `Enum` listing the possible modes of the main window."""

    LIST = "list"
    """This mode is the default one and contains output from a `cobib.commands.list.ListCommand`."""
    SHOW = "show"
    """This mode contains output from a `cobib.commands.show.ShowCommand`."""
    SEARCH = "search"
    """This mode contains output from a `cobib.commands.search.SearchCommand`."""


class State:
    """An object to track the stateful parameters of coBib's TUI.

    This object is used to store all stateful parameters of coBib's TUI and simplify the handling of
    these parameters across the TUI and Frame objects.
    """

    def __init__(self) -> None:
        """Initializes the State object."""
        LOGGER.debug("Initializing the State")
        self.top_line: int = 0
        """The line number at the top of the visible window."""
        self.left_edge: int = 0
        """The column number at the left edge of the visible window."""
        self.current_line: int = 0
        """The currently selected line number."""
        self.previous_line: int = -1
        """The previous line number. This is used when switching back to a previous `Mode`."""

        self.mode: str = Mode.LIST.value
        """The window's current `Mode`."""
        self.inactive_commands: List[str] = []
        """A list of disabled commands. For example the *Search* Mode disables the `Add`, `Filter`
        and `Sort` commands."""
        self.topstatus: str = ""
        """The contents of the top statusbar."""

        # these cannot be set yet, because the `config` has not been fully populated at the time of
        # creation of the STATE singleton
        self.list_args: List[str] = []
        """The current arguments for the `cobib.commands.list.ListCommand` populating the default
        *List* Mode. This variable is crucial for the handling of the `Sort` and `Filter`
        commands."""

    def reset(self) -> None:
        """Resets the state to its original starting point."""
        LOGGER.debug("Resetting the State")
        self.top_line = 0
        self.left_edge = 0
        self.current_line = 0
        self.previous_line = -1

        self.mode = Mode.LIST.value
        self.inactive_commands = []
        self.topstatus = ""

        self.initialize()

    def initialize(self) -> None:
        """Initializes the configuration-dependent settings."""
        self.list_args = config.tui.default_list_args
        if config.tui.reverse_order:
            self.list_args += ["-r"]

    def update(self, state: State) -> None:
        """Update from another State.

        This overwrites this State with the contents of another one.

        Args:
            state: another (deep-copied) state.
        """
        self.top_line = state.top_line
        self.left_edge = state.left_edge
        self.current_line = state.current_line
        self.previous_line = state.previous_line

        self.mode = state.mode
        self.inactive_commands = state.inactive_commands
        self.topstatus = state.topstatus

        self.list_args = state.list_args


STATE = State()
"""coBib's main-runtime State instance."""
