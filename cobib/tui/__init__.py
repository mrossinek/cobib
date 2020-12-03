"""CoBib TUI module."""

import curses

from .buffer import TextBuffer, InputBuffer
from .tui import TUI


__all__ = ["TUI",
           "TextBuffer",
           "InputBuffer"]


def tui():
    """Main executable for the curses-TUI."""
    curses.wrapper(TUI)
