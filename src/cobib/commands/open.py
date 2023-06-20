"""coBib's Open command.

This command can be used to open associated file(s) of one (or multiple) entries.
```
cobib open <label 1> [<label 2> ...]
```

The keys of `cobib.database.Entry.data` which are queried for paths or URL strings can be configured
via the `cobib.config.config.OpenCommandConfig.fields` setting (defaulting to `["file", "url"]`).
If one such string is found, it is automatically opened with the program configured by
`cobib.config.config.OpenCommandConfig.command`.
If multiple matches are found, the user will be presented with a menu to choose one or multiple
matches.

This menu will look similar to the following after querying for `help`:
```
Multiple targets were found. You may select the following:
  1. an individual URL number
  2. a target type (provided in '[...]')
  3. 'all'
  4. or 'cancel' to abort the command

  1: [file] /path/to/a/file.pdf
  2: [file] /path/to/another/file.pdf
  3: [url] https://example.org/
[all,help,cancel]:
```

With the above options, here is what will happen depending on the users choice:
* `1`, `2`, or `3`: will open the respective file or URL.
* `file` or `url`: will open the respective group.
* `all`: will open all matches.
* `help`: will print the detailed help-menu again.
* `cancel`: will abort the command.

### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `o` key.
"""

from __future__ import annotations

import logging
import os
import subprocess
import warnings
from collections import defaultdict
from functools import wraps
from typing import Callable, cast
from urllib.parse import ParseResult, urlparse

from rich.console import Console
from rich.prompt import InvalidResponse, Prompt, PromptBase, PromptType
from rich.text import Text
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class OpenCommand(Command):
    """The Open Command.

    This command can parse the following arguments:

        * `labels`: one (or multiple) labels of the entries to be opened.
    """

    name = "open"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="open", description="Open subcommand parser.")
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        cls.argparser = parser

    # TODO: can we make the implementation cleaner and avoid the type ignore comment below?
    @override
    async def execute(self) -> None:  # type: ignore[override]
        # pylint: disable=invalid-overridden-method
        LOGGER.debug("Starting Open command.")

        Event.PreOpenCommand.fire(self)

        bib = Database()

        for label in self.largs.labels:
            things_to_open: dict[str, list[ParseResult]] = defaultdict(list)
            count = 0
            # first: find all possible things to open
            try:
                entry = bib[label]
                for field in config.commands.open.fields:
                    if field in entry.data.keys() and entry.data[field]:
                        value = entry.data[field]
                        if not isinstance(value, list):
                            value = [value]
                        for val in value:
                            val = val.strip()
                            LOGGER.debug('Parsing "%s" for URLs.', val)
                            things_to_open[field] += [urlparse(val)]
                            count += 1
            except KeyError:
                msg = f"No entry with the label '{label}' could be found."
                LOGGER.warning(msg)
                continue

            # if there are none, skip current label
            if not things_to_open:
                msg = f"The entry '{label}' has no actionable field associated with it."
                LOGGER.warning(msg)
                continue

            if count == 1:
                # we found a single URL to open
                self._open_url(list(things_to_open.values())[0][0])
            else:
                # we query the user what to do
                idx = 0
                url_list: list[ParseResult] = []
                prompt_text = Text()
                choices = ["all"] + config.commands.open.fields + ["help", "cancel"]

                # print formatted list of available URLs
                for field, urls in things_to_open.items():
                    for url in urls:
                        idx += 1
                        url_list.append(url)
                        choices.append(str(idx))
                        prompt_text.append(f"{idx:3}", "prompt.choices")
                        prompt_text.append(": [")
                        prompt_text.append(field, "prompt.choices")
                        prompt_text.append(f"] {url.geturl()}\n")
                prompt_text.append("[all,help,cancel]", "prompt.choices")

                # pylint: disable=line-too-long
                self.prompt.process_response = self._wrap_prompt_process_response(  # type: ignore[method-assign]
                    self.prompt.process_response  # type: ignore[assignment]
                )
                if self.prompt is not Prompt:
                    choice = await self.prompt.ask(  # type: ignore[call-overload]
                        prompt_text,
                        choices=choices,
                        show_choices=False,
                        console=cast(App[None], self.console),
                    )
                else:
                    choice = self.prompt.ask(
                        prompt_text,
                        choices=choices,
                        show_choices=False,
                        console=cast(Console, self.console),
                    )

                self.prompt.process_response = (  # type: ignore[method-assign]
                    self.prompt.process_response.__wrapped__  # type: ignore[attr-defined]
                )

                if choice == "cancel":
                    LOGGER.warning("User aborted open command.")
                elif choice == "all":
                    LOGGER.debug("User selected all urls.")
                    for url in url_list:
                        self._open_url(url)
                elif choice in things_to_open.keys():
                    LOGGER.debug("User selected the %s set of urls.", choice)
                    for url in things_to_open[choice]:
                        self._open_url(url)
                elif choice.isdigit():
                    LOGGER.debug("User selected url %s", choice)
                    self._open_url(url_list[int(choice) - 1])

        Event.PostOpenCommand.fire(self)

    @staticmethod
    def _open_url(url: ParseResult) -> None:
        """Opens a URL.

        Args:
            url: the URL to be opened.
        """
        opener = config.commands.open.command
        try:
            url_str: str = url.geturl() if url.scheme else str(RelPath(url.geturl()).path)
            LOGGER.debug('Opening "%s" with %s.', url_str, opener)
            with open(os.devnull, "w", encoding="utf-8") as devnull:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=ResourceWarning)
                    subprocess.Popen(  # pylint: disable=consider-using-with
                        [opener, url_str],
                        stdout=devnull,
                        stderr=devnull,
                        stdin=devnull,
                        close_fds=True,
                    )
        except FileNotFoundError as err:
            LOGGER.error(err)

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

            if return_value == "help":
                LOGGER.debug("User requested help.")
                raise InvalidResponse(
                    "[yellow]Multiple targets were found. You may select the following:\n"
                    "  1. an individual URL number\n"
                    "  2. a target type (provided in '[...]')\n"
                    "  3. 'all'\n"
                    "  4. or 'cancel' to abort the command"
                )

            return return_value

        return process_response
