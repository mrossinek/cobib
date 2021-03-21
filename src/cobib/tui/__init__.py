"""coBib TUI module."""

import curses

from .buffer import InputBuffer, TextBuffer
from .frame import Frame
from .state import Mode, State
from .tui import TUI


def tui():
    """Main executable for the curses-TUI."""
    curses.wrapper(TUI)
