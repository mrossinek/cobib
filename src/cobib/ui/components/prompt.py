"""coBib's prompt widget.

This widget implements rich's
[`PromptBase`](https://rich.readthedocs.io/en/stable/reference/prompt.html#rich.prompt.PromptBase).
It renders the actual user prompt as a `cobib.ui.components.popup.Popup` and accepts the response
via a `cobib.ui.components.input.Input` widget.

This implementation permits the seamless integration of interactive user prompts during command
execution with an interactive TUI based on textual.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TextIO

from rich.prompt import InvalidResponse, PromptBase
from rich.text import Text, TextType
from typing_extensions import override

from .input import Input
from .popup import Popup

if TYPE_CHECKING:
    from ..tui import TUI


class Prompt(PromptBase[str]):
    """coBib's prompt widget."""

    console: TUI  # type: ignore[assignment]
    """The running TUI instance. This overloads the meaning of `console` in rich's understanding."""

    help_popup: Popup | None = None
    """A reference to the popup with help contents if the user requested such."""

    # pylint: disable=invalid-overridden-method
    @override
    async def __call__(  # type: ignore[override]
        self, *, default: Any = ..., stream: TextIO | None = None
    ) -> str:
        popup: Popup
        reply: str
        while True:
            self.pre_prompt()
            prompt = self.make_prompt(default)
            prompt.rstrip()
            popup = Popup(prompt + "\n", level=0, timer=None)
            self.console.print(popup)
            value = await self.get_input(self.console, prompt, self.password, stream=stream)
            await popup.remove()
            if value == "" and default != ...:
                reply = str(default)
                break
            try:
                return_value = self.process_response(value)
            except InvalidResponse as error:
                self.on_validate_error(value, error)
                continue
            else:
                reply = return_value
                break
        if self.help_popup is not None:
            self.help_popup.remove()
        return reply

    # pylint: disable=invalid-overridden-method
    @override
    @classmethod
    async def get_input(  # type: ignore[override]
        cls, console: TUI, prompt: TextType, password: bool, stream: TextIO | None = None
    ) -> str:
        inp = Input()
        inp.catch = True
        inp.styles.layer = "overlay"
        inp.styles.dock = "bottom"  # type: ignore[arg-type]
        inp.styles.border = (None, None)
        inp.styles.padding = (0, 0)
        await console.mount(inp)

        inp.focus()

        while console.is_mounted(inp):
            await asyncio.sleep(0)

        return str(inp.value)

    @override
    def on_validate_error(self, value: str, error: InvalidResponse) -> None:
        if value == "help":
            if self.help_popup is not None:
                self.help_popup.remove()
            if isinstance(error.message, Text):
                popup = Popup(error.message + "\n", level=0, timer=None)
            else:
                popup = Popup(Text.from_markup(error.message + "\n"), level=0, timer=None)
            self.console.print(popup)
            self.help_popup = popup
        else:
            super().on_validate_error(value, error)
