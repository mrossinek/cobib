"""Methods and classes to mock a coBib TUI."""

import logging
from typing import Dict, Set

from .mock_curses import MockCursesPad


class MockTUI:
    """Mock cobib.tui.TUI implementation."""

    # pylint: disable=missing-function-docstring,unused-argument

    ANSI_MAP: Dict[str, int] = {}

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
