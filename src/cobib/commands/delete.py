"""coBib's Delete command.

This command can be used to deleted entries from the database.
```
cobib delete <label 1> [<label 2> ...]
```

When you delete an entry, the value of `cobib.config.config.DeleteCommandConfig.preserve_files`
setting (added in v4.1.0) determines whether the associated files will be deleted, too. This
defaults to `False`, meaning that they *will* be deleted. You can overwrite the value of this
setting at runtime with the `--preserve-files` and `--no-preserve-files` arguments, respectively.
I.e. the following will **not** delete your files:
```
cobib delete --preserve-files <label 1> [<label 2> ...]
```
While this command will always delete them:
```
cobib delete --no-preserve-files <label 1> [<label 2> ...]
```

As of coBib v4.1.0, the user will be asked to confirm the deletion via an interactive prompt. This
can be disabled by setting `cobib.config.config.DeleteCommandConfig.confirm` to `False`.

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `d` key.
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Callable, Set, Type, cast

from rich.console import Console
from rich.prompt import Confirm, InvalidResponse, PromptBase, PromptType
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class DeleteCommand(Command):
    """The Delete Command.

    This command can parse the following arguments:

        * `labels`: one (or multiple) labels of the entries to be deleted.
        * `--preserve-files`: skips the deletion of any associated files. This overwrites the
          `cobib.config.config.DeleteCommandConfig.preserve_files` setting.
        * `--no-preserve-files`: does NOT skip the deletion of any associated files. This overwrites
          the `cobib.config.config.DeleteCommandConfig.preserve_files` setting.
    """

    name = "delete"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: Type[PromptBase[PromptType]] | None = None,
    ) -> None:
        if prompt is None:
            prompt = Confirm  # type: ignore[assignment]

        super().__init__(*args, console=console, prompt=prompt)

        self.deleted_entries: Set[str] = set()
        """A set of labels which were deleted by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="delete", description="Delete subcommand parser.")
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        preserve_files_group = parser.add_mutually_exclusive_group()
        preserve_files_group.add_argument(
            "--preserve-files",
            action="store_true",
            default=None,
            help="do not delete associated files",
        )
        preserve_files_group.add_argument(
            "--no-preserve-files",
            dest="preserve_files",
            action="store_false",
            default=None,
            help="delete associated files",
        )
        cls.argparser = parser

    @override
    async def execute(self) -> None:  # type: ignore[override]
        # pylint: disable=invalid-overridden-method
        LOGGER.debug("Starting Delete command.")

        Event.PreDeleteCommand.fire(self)

        preserve_files = config.commands.delete.preserve_files
        if self.largs.preserve_files is not None:
            preserve_files = self.largs.preserve_files
        LOGGER.info("Associated files will%s be preserved.", "" if preserve_files else " not")

        # pylint: disable=line-too-long
        self.prompt.process_response = self._wrap_prompt_process_response(  # type: ignore[method-assign]
            self.prompt.process_response  # type: ignore[assignment]
        )

        bib = Database()
        for label in self.largs.labels:
            try:
                LOGGER.debug("Attempting to delete entry '%s'.", label)

                if config.commands.delete.confirm:
                    prompt_text = f"Are you sure you want to delete the entry '{label}'?"

                    if self.prompt is not Confirm:
                        res = await self.prompt.ask(  # type: ignore[call-overload]
                            prompt_text,
                            choices=["y", "n"],
                            default="y",
                            console=cast(App[None], self.console),
                        )
                    else:
                        res = self.prompt.ask(
                            prompt_text,
                            default=True,
                            console=cast(Console, self.console),
                        )

                    if not res:
                        continue

                entry = bib.pop(label)
                if not preserve_files:
                    for file in entry.file:
                        path = RelPath(file)
                        try:
                            LOGGER.debug("Attempting to remove associated file '%s'.", str(path))
                            os.remove(path.path)
                        except FileNotFoundError:
                            pass

                self.deleted_entries.add(label)
            except KeyError:
                pass

        self.prompt.process_response = (  # type: ignore[method-assign]
            self.prompt.process_response.__wrapped__  # type: ignore[attr-defined]
        )

        Event.PostDeleteCommand.fire(self)
        bib.save()

        self.git()

        for label in self.deleted_entries:
            msg = f"'{label}' was removed from the database."
            LOGGER.info(msg)

    @staticmethod
    def _wrap_prompt_process_response(
        func: Callable[[PromptBase[PromptType], str], PromptType]
    ) -> Callable[[PromptBase[PromptType], str], PromptType]:
        """A method to wrap a `PromptBase.process_response` method.

        This method wraps a `PromptBase.process_response` method in order to handle a user's request
        for additional help.

        Args:
            func: the `PromptBase.process_response` method to be wrapped.

        Returns:
            The wrapped `PromptBase.process_response` method.
        """

        @override  # type: ignore[misc]
        @wraps(func)
        def process_response(prompt: PromptBase[PromptType], value: str) -> PromptType:
            return_value: PromptType = func(prompt, value)

            if isinstance(return_value, bool):
                return return_value  # type: ignore[return-value]

            if cast(str, return_value).strip().lower() == "y":
                return True  # type: ignore[return-value]

            if cast(str, return_value).strip().lower() == "n":
                return False  # type: ignore[return-value]

            raise InvalidResponse("You may only provide 'y' or 'n' as a valid response.")

        return process_response
