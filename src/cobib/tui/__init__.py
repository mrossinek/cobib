"""coBib's TUI module.

This module implements coBib's curses-based TUI.
The code is split into several submodules:
* `cobib.tui.buffer`: implements a general `TextBuffer` and `InputBuffer` to handle in- and output.
* `cobib.tui.frame`: implements the `Frame` class which tightly couples a `TextBuffer` to a
  `curses.pad` and is used by the `TUI` as the main interaction window.
* `cobib.tui.state`: gathers the stateful-information of the `TUI` in a simple object.
* `cobib.tui.tui.TUI`: implements the actual TUI.
"""

import curses

from .buffer import InputBuffer as InputBuffer
from .buffer import TextBuffer as TextBuffer
from .frame import Frame as Frame
from .state import Mode as Mode
from .state import State as State
from .tui import TUI as TUI


def tui() -> None:
    """The main executable for the curses-TUI.

    This method is the entry-point for coBib's TUI.
    It simply passes the `cobib.tui.tui.TUI` initializer to the `curses.wrapper` method which takes
    care of all the rest.
    """
    curses.wrapper(TUI)  # pragma: no cover
