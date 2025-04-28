"""coBib's log screen.

This screen renders the log messages.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import RichLog, Static
from typing_extensions import override


class LogScreen(ModalScreen[None]):
    """coBib's log screen."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("z", "toggle_log", "log"),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | z | Toggles the log screen. |
    """

    DEFAULT_CSS = """
        LogScreen {
            align: center bottom;
            offset-y: -1;
        }

        #caption {
            background: $surface;
        }

        #log {
            height: auto;
            max-height: 50%;
            background: $surface;
        }
    """

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.rich_log = RichLog(id="log")
        """The internal `RichLog` widget in which the actual log messages are rendered."""

    @override
    def compose(self) -> ComposeResult:
        yield self.rich_log
        yield Static(
            "These are your log messages. Press 'z' to close this screen.",
            id="caption",
        )

    def action_toggle_log(self) -> None:
        """Toggles the log.

        Since this is the action of the `LogScreen`, it simply pops the screen.
        """
        assert self.is_current
        self.app.pop_screen()
