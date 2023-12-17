"""coBib's prompt widget.

This widget implements rich's
[`PromptBase`](https://rich.readthedocs.io/en/stable/reference/prompt.html#rich.prompt.PromptBase).

It leverages coBib's `cobib.ui.components.input_screen.InputScreen` for handling user input.

This implementation permits the seamless integration of interactive user prompts during command
execution with an interactive TUI based on textual.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TextIO, cast

from rich.prompt import InvalidResponse, PromptBase
from rich.text import Text, TextType
from textual.widgets import Input, Static
from typing_extensions import override

from .input_screen import InputScreen

if TYPE_CHECKING:
    from ..tui import TUI


class Prompt(PromptBase[str]):
    """coBib's prompt widget."""

    console: TUI  # type: ignore[assignment]
    """The running TUI instance. This overloads the meaning of `console` in rich's understanding."""

    @override
    async def __call__(  # type: ignore[override]
        self, *, default: Any = ..., stream: TextIO | None = None
    ) -> str:
        while True:
            self.pre_prompt()
            prompt = self.make_prompt(default)
            value = await self.get_input(self.console, prompt, self.password, stream=stream)
            if value == "" and default != ...:
                return str(default)
            try:
                return_value = self.process_response(value)
            except InvalidResponse as error:
                self.on_validate_error(value, error)
                continue
            else:
                return return_value

    @override
    @classmethod
    async def get_input(  # type: ignore[override]
        cls, console: TUI, prompt: TextType, password: bool, stream: TextIO | None = None
    ) -> str:
        dismiss_event = asyncio.Event()
        value = ""

        def _catch_dismissed_value(val: str) -> None:
            nonlocal value
            value = val
            dismiss_event.set()

        popup = Static(prompt + "\n", id="prompt")

        inp_screen = cast(InputScreen, console.get_screen("input"))
        inp_screen.escape_enabled = False

        if inp_screen.is_current:
            # We need to pop the screen first to ensure that we can register our result callback.
            # The reason it might be the current screen already is if the pre_prompt has pushed it.
            console.pop_screen()

        await_mount = console.push_screen("input", _catch_dismissed_value)
        inp_screen.mount(popup, before=-1)
        await await_mount

        inp_screen.query_one(Input).value = ""
        await dismiss_event.wait()
        return value

    @override
    def on_validate_error(self, value: str, error: InvalidResponse) -> None:
        _id = "help" if value == "help" else "error"
        if isinstance(error.message, Text):
            message = Static(error.message, id=_id)
        else:
            message = Static(Text.from_markup(error.message), id=_id)

        self.console.get_screen("input").mount(message, before=-1)
