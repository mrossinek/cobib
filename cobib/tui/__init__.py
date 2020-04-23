"""CoBib TUI module"""

import curses

from .tui import TUI


__all__ = ["TUI"]


def tui():
    """Main executable for the curses-TUI."""
    curses.wrapper(TUI)
