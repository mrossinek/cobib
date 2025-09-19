"""coBib's global console instance.

See the suggestion in rich's documentation: https://rich.readthedocs.io/en/stable/console.html.
"""

from __future__ import annotations

from getpass import getpass
from typing import Any, TextIO

from rich.console import Console
from rich.text import TextType
from typing_extensions import override

from cobib.config import config
from cobib.utils.rel_path import RelPath

HAS_OPTIONAL_PROMPT_TOOLKIT = False
"""Whether the optional `prompt_toolkit` dependency is installed."""

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory, InMemoryHistory
except ModuleNotFoundError:  # pragma: no cover
    pass
else:
    HAS_OPTIONAL_PROMPT_TOOLKIT = True


class PromptConsole(Console):
    """A wrapper of a `rich.console.Console` to integrate it with a `prompt_toolkit.PromptSession`.

    This enables more powerful line editing during input prompts with fewer compatibility issues
    than Python's builtin `readline` module and `rich`.
    """

    _instance: PromptConsole | None = None
    """The singleton instance of this class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes a new console instance.

        Args:
            args: arbitrary positional arguments for the `rich.Console`.
            kwargs: arbitrary keyword arguments for the `rich.Console`.
        """
        if "theme" not in kwargs:  # pragma: no branch
            kwargs["theme"] = config.theme.build()

        super().__init__(*args, **kwargs)

        self.prompt_session: PromptSession[str] | None = None
        """The `prompt-toolkit` session of this console. When this optional dependency is not
        installed, this will be `None` and the builtin `input()` function will be used instead."""

        # NOTE: branch coverage dealt with separately
        if HAS_OPTIONAL_PROMPT_TOOLKIT:  # pragma: no branch
            self.prompt_session = PromptSession(
                history=InMemoryHistory()
                if config.shell.history is None
                else FileHistory(RelPath(config.shell.history).path),
                vi_mode=config.shell.vi_mode,
            )

    @classmethod
    def get_instance(cls) -> PromptConsole:
        """Singleton constructor.

        Returns:
            The singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    @classmethod
    def clear_instance(cls) -> None:
        """Clears the singleton instance.

        This is most likely only useful in the context of unittesting.
        """
        cls._instance = None

    @override
    async def input(  # type: ignore[override]
        self,
        prompt: TextType = "",
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: TextIO | None = None,
    ) -> str:
        # NOTE: we override this method to replace rich's call to Python's input() method with a
        # call to prompt_toolkit's prompt_async() method
        if prompt:  # pragma: no branch
            if self.prompt_session is None:
                self.print(prompt, markup=markup, emoji=emoji, end="")  # pragma: no cover
            else:
                with self.capture() as capture:
                    self.print(prompt, markup=markup, emoji=emoji, end="")
                prompt_str = capture.get()
        if password:
            result = getpass("", stream=stream)  # pragma: no cover
        elif stream:
            result = stream.readline()  # pragma: no cover
        elif self.prompt_session is None:
            result = input()  # pragma: no cover
        else:
            result = await self.prompt_session.prompt_async(prompt_str)
        return result

    @override
    def clear_live(self) -> None:
        super().clear_live()
        # NOTE: this ensures that the console resets properly in the unittest suite during which an
        # attempt would be made to reuse a partially torn down instance of this console.
        self.clear_instance()
