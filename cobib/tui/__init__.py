"""CoBib TUI module."""

import curses

from .tui import TextBuffer
from .tui import TUI


__all__ = ["TextBuffer", "TUI"]


def tui():
    """Main executable for the curses-TUI."""
    curses.wrapper(TUI)
