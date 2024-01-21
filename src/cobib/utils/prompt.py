"""coBib's Rich-Textual prompt integration.

The `Prompt` utility of this module either constructs a `rich.prompt.Prompt` or a custom textual
widget to prompt the user for input. In the latter case, it leverages coBib's
`cobib.ui.components.input_screen.InputScreen` for handling the input.

This implementation permits the seamless integration of interactive user prompts during command
execution with an interactive TUI based on textual.

The `Confirm` utility provides an even simpler interface for yes/no prompts.
"""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any, Callable, TextIO, Type, cast

from rich.console import RenderableType
from rich.prompt import Confirm as RichConfirm
from rich.prompt import InvalidResponse, PromptBase, PromptType
from rich.prompt import Prompt as RichPrompt
from rich.text import Text, TextType
from textual.app import App
from textual.widgets import Input, Static
from typing_extensions import override

from .context import get_active_app


class Prompt:
    """A utility class to construct either a `rich` or `textual` prompt."""

    @staticmethod
    async def ask(
        prompt: TextType = "",
        *,
        choices: list[str] | None = None,
        default: Any = ...,
        show_choices: bool = True,
        show_default: bool = True,
        input_text: str = "",
        pre_prompt_message: RenderableType | None = None,
        process_response_wrapper: Callable[
            [Callable[[PromptBase[PromptType], str], PromptType]],
            Callable[[PromptBase[PromptType], str], PromptType],
        ]
        | None = None,
    ) -> Any:
        """Exposes the `rich.prompt.Prompt.ask` method.

        Args:
            prompt: the text for the prompt.
            choices: an optional list of choices.
            default: an optional default choice.
            show_choices: whether to display the choices (if any).
            show_default: whether to display the default choice.
            input_text: the text with which to pre-populate the input prompt.
            pre_prompt_message: a renderable message to display before the prompt.
            process_response_wrapper: a function to wrap the `rich.prompt.Prompt.process_response`
                method to allow the calling scope to inject response handling logic.
        """
        ask_prompt: Type[RichPrompt | TextualPrompt] = RichPrompt
        app = get_active_app()
        if app is not None:
            ask_prompt = TextualPrompt
            ask_prompt.input_text = input_text

        if process_response_wrapper is not None:
            ask_prompt.process_response = process_response_wrapper(  # type: ignore[assignment]
                ask_prompt.process_response  # type: ignore[arg-type]
            )

        if pre_prompt_message is not None:
            ask_prompt.pre_prompt = Prompt._wrap_pre_prompt(  # type: ignore[assignment]
                ask_prompt.pre_prompt, pre_prompt_message
            )

        if app is not None:
            res = await ask_prompt.ask(  # type: ignore[call-overload]
                prompt,
                choices=choices,
                default=default,
                show_choices=show_choices,
                show_default=show_default,
                console=app,
            )
        else:
            res = ask_prompt.ask(
                prompt,
                choices=choices,
                default=default,
                show_choices=show_choices,
                show_default=show_default,
            )

        if process_response_wrapper is not None:
            ask_prompt.process_response = (  # type: ignore[method-assign]
                ask_prompt.process_response.__wrapped__  # type: ignore[attr-defined]
            )

        if pre_prompt_message is not None:
            ask_prompt.pre_prompt = (  # type: ignore[method-assign]
                ask_prompt.pre_prompt.__wrapped__  # type: ignore[attr-defined]
            )

        return res

    @staticmethod
    def _wrap_pre_prompt(
        func: Callable[[PromptBase[PromptType]], None], message: RenderableType
    ) -> Callable[[PromptBase[PromptType]], None]:
        @wraps(func)
        def pre_prompt(prompt: PromptBase[PromptType]) -> None:
            app = get_active_app()
            if app is None:
                prompt.console.print(message)
            else:
                input_screen = app.get_screen("input")
                input_screen.mount(Static(message, id="panel"), before=-1)

        return pre_prompt


class Confirm:
    """A utility class to construct a yes/no `Prompt`."""

    @staticmethod
    async def ask(
        prompt: TextType = "",
        *,
        default: bool,
    ) -> bool:
        """Exposes the `rich.prompt.Confirm.ask` method.

        Args:
            prompt: the text for the prompt.
            default: the default answer.
        """
        confirm_prompt: Type[RichConfirm | TextualPrompt] = RichConfirm
        app = get_active_app()
        if app is not None:
            confirm_prompt = TextualPrompt

        confirm_prompt.process_response = Confirm._wrap_process_response(  # type: ignore[assignment]
            confirm_prompt.process_response  # type: ignore[arg-type]
        )

        if app is None:
            res = confirm_prompt.ask(prompt, default=default)
        else:
            res = await confirm_prompt.ask(  # type: ignore[call-overload]
                prompt, console=app, choices=["y", "n"], default="y" if default else "n"
            )

        confirm_prompt.process_response = (  # type: ignore[method-assign]
            confirm_prompt.process_response.__wrapped__  # type: ignore[union-attr]
        )

        return cast(bool, res)

    @staticmethod
    def _wrap_process_response(
        func: Callable[[PromptBase[bool], str], bool],
    ) -> Callable[[PromptBase[bool], str], bool]:
        @wraps(func)
        def process_response(prompt: PromptBase[bool], value: str) -> bool:
            return_value: bool = func(prompt, value)

            if isinstance(return_value, bool):
                return return_value

            if cast(str, return_value).strip().lower() == "y":
                return True

            if cast(str, return_value).strip().lower() == "n":
                return False

            raise InvalidResponse("You may only provide 'y' or 'n' as a valid response.")

        return process_response


class TextualPrompt(PromptBase[str]):
    """coBib's prompt widget."""

    input_text: str = ""
    """The text to pre-populate the input prompt with."""

    @override
    async def __call__(  # type: ignore[override]
        self, *, default: Any = ..., stream: TextIO | None = None
    ) -> str:
        while True:
            self.pre_prompt()
            prompt = self.make_prompt(default)
            value = await self.get_input(self.console, prompt, self.password, stream=stream)  # type: ignore[arg-type]
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
        cls, console: App[None], prompt: TextType, password: bool, stream: TextIO | None = None
    ) -> str:
        dismiss_event = asyncio.Event()
        value = ""

        def _catch_dismissed_value(val: str) -> None:
            nonlocal value
            value = val
            dismiss_event.set()

        popup = Static(prompt + "\n", id="prompt")

        inp_screen = console.get_screen("input")
        # This is an cobib.ui.tui.components.InputScreen but casting to it would result in a
        # circular import. Instead, we ignore the mypy warning below.
        inp_screen.escape_enabled = False  # type: ignore[attr-defined]

        if inp_screen.is_current:
            # We need to pop the screen first to ensure that we can register our result callback.
            # One reason it might be the current screen already is if the pre_prompt has pushed it.
            console.pop_screen()

        await_mount = console.push_screen("input", _catch_dismissed_value)
        inp_screen.mount(popup, before=-1)
        await await_mount

        inp_screen.query_one(Input).value = cls.input_text
        await dismiss_event.wait()
        return value

    @override
    def on_validate_error(self, value: str, error: InvalidResponse) -> None:
        _id = "help" if value == "help" else "error"
        if isinstance(error.message, Text):
            message = Static(error.message, id=_id)
        else:
            message = Static(Text.from_markup(error.message), id=_id)

        self.console.get_screen("input").mount(message, before=-1)  # type: ignore[attr-defined]
