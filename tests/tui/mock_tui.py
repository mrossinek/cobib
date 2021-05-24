"""Mocking utilities for the `cobib.tui.tui.TUI`."""
# pylint: disable=missing-function-docstring,unused-argument

import logging
from typing import Dict, Set

from .mock_curses import MockCursesPad


class MockTUI:
    """This class mocks the `cobib.tui.tui.TUI`.

    When testing the `cobib.tui` modules, we need full control. Thus, this class removes all of the
    non-essential aspects and logs all method calls.
    """

    ANSI_MAP: Dict[str, int] = {}
    """The `ANSI_MAP` exists as part of `cobib.tui.tui.TUI` and will be populated at runtime."""

    def __init__(self) -> None:
        # noqa: D107
        self.height = 20
        self.width = 40
        self.prompt = MockCursesPad()
        self.selection: Set[str] = set()
        self.topbar = None
        self.logger = logging.getLogger("MockTUI")

    def prompt_handler(self, *args, **kwargs):  # type: ignore
        # noqa: D102
        self.logger.debug("prompt_handler")

    def resize_handler(self, *args):  # type: ignore
        # noqa: D102
        self.logger.debug("resize_handler")

    def statusbar(self, *args):  # type: ignore
        # noqa: D102
        self.logger.debug("statusbar")
