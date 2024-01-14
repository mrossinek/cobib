"""coBib's input screen.

This screen is an interactive input screen. It automatically focuses the central `Input` widget but
also provides panels to displays user prompts, help information and other popups.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Static
from typing_extensions import override


class InputScreen(ModalScreen[str]):
    """coBib's input screen."""

    AUTO_FOCUS = "Input"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("escape", "escape", "Quit the prompt")
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | escape | When enabled, quits the interactive input screen. |
    """

    DEFAULT_CSS = """
        InputScreen {
            align: center middle;
        }

        #input {
            padding: 1 2;
            width: 80%;
            height: auto;
            background: $surface;
        }

        #prompt {
            padding: 1 2;
            width: 80%;
            height: auto;
            background: $surface;
        }

        #help {
            padding: 1 2;
            width: 80%;
            height: auto;
            background: $surface;
        }

        #error {
            padding: 1 2;
            width: 80%;
            height: auto;
            background: red 20%;
        }

        #panel {
            padding: 1 2;
            width: 80%;
            height: auto;
            background: $surface;
        }
    """

    escape_enabled: bool = True
    """Enables the `escape` key binding."""

    @override
    def compose(self) -> ComposeResult:
        inp = Input(id="input")
        yield inp

    async def action_escape(self) -> None:
        """The action to perform when the `Escape` key is pressed."""
        if self.escape_enabled:
            self.dismiss("")
            await self.query(Static).remove()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """The action to perform when receiving the `Submitted` event.

        In this case, unmount the widget itself if `catch` is set. Otherwise the event gets
        [bubbled up](https://textual.textualize.io/guide/events/#bubbling).
        """
        self.dismiss(event.input.value)
        await self.query(Static).remove()
        event.stop()
