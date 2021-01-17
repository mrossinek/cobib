"""CoBib's TUI state."""

import logging

from enum import Enum

from cobib.config import config

LOGGER = logging.getLogger(__name__)


class Mode(Enum):
    """The possible view modes."""
    LIST = 'list'
    SHOW = 'show'
    SEARCH = 'search'


class State:
    """State class to track the stateful parameters of CoBib's TUI.

    State objects are used to store all stateful parameters of CoBib's TUI and simplify the handling
    of these parameters across the TUI and Frame objects.
    """

    def __init__(self):
        """Initializes the State object."""
        LOGGER.debug('Initializing the State')
        self.top_line = 0
        self.left_edge = 0
        self.current_line = 0
        self.previous_line = -1

        self.mode = Mode.LIST.value
        self.inactive_commands = []
        self.topstatus = ''

        # these cannot be set yet, because the `config` has not been fully populated at the time of
        # creation of the STATE singleton
        self.list_args = []

    def initialize(self):
        """Initialize configuration-dependent settings."""
        self.list_args = config.tui.default_list_args
        if config.tui.reverse_order:
            self.list_args += ['-r']

    def update(self, state):
        """Update from other state.

        Args:
            state (State): another (deep-copied) state.
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
