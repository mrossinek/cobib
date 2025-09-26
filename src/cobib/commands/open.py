"""Open associated files.

.. include:: ../man/cobib-open.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
import os
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from urllib.parse import ParseResult, urlparse

from rich.prompt import InvalidResponse, PromptBase, PromptType
from rich.text import Text
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.context import get_active_app
from cobib.utils.prompt import Prompt
from cobib.utils.rel_path import RelPath

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class OpenCommand(Command):
    """The Open Command.

    This command can parse the following arguments:

        * `labels`: one (or multiple) labels of the entries to be opened.
        * `-f`, `--field`: specifies the field to be opened, bypassing the interactive prompt.
    """

    name = "open"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.opened_entries: set[str] = set()
        """The set of labels corresponding to the entries which were opened by this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="open",
            description="Open subcommand parser.",
            epilog="Read cobib-open.1 for more help.",
        )
        parser.add_argument("labels", type=str, nargs="+", help="labels of the entries")
        parser.add_argument(
            "-f",
            "--field",
            type=str,
            choices=["all", *config.commands.open.fields],
            help="which field to open in case multiple are found",
        )
        cls.argparser = parser

    # TODO: can we make the implementation cleaner and avoid the type ignore comment below?
    @override
    async def execute(self) -> None:  # type: ignore[override]  # noqa: PLR0912
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
                            val = val.strip()  # noqa: PLW2901
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
                success = self.open(next(iter(things_to_open.values()))[0])
                if success:
                    self.opened_entries.add(label)

            elif self.largs.field is not None:
                choice = self.largs.field
                LOGGER.debug("User selected the %s set of urls from the CLI.", choice)

                if choice == "all":
                    for urls in things_to_open.values():
                        for url in urls:
                            success = self.open(url)
                            if success:
                                self.opened_entries.add(label)

                elif choice in things_to_open.keys():
                    for url in things_to_open[choice]:
                        success = self.open(url)
                        if success:
                            self.opened_entries.add(label)

                else:
                    msg = (  # pragma: no cover
                        f"The entry '{label}' has no field '{choice}' associated with it."
                    )
                    LOGGER.warning(msg)  # pragma: no cover
                    continue  # pragma: no cover

            else:
                # we query the user what to do
                idx = 0
                url_list: list[ParseResult] = []
                prompt_text = Text()
                choices = ["all", *config.commands.open.fields, "help", "cancel"]

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

                choice = await Prompt.ask(
                    prompt_text,
                    choices=choices,
                    show_choices=False,
                    process_response_wrapper=self._wrap_prompt_process_response,
                )

                if choice == "cancel":
                    LOGGER.warning("User aborted open command.")
                elif choice == "all":
                    LOGGER.debug("User selected all urls.")
                    for url in url_list:
                        success = self.open(url)
                        if success:
                            self.opened_entries.add(label)
                elif choice in things_to_open.keys():
                    LOGGER.debug("User selected the %s set of urls.", choice)
                    for url in things_to_open[choice]:
                        success = self.open(url)
                        if success:
                            self.opened_entries.add(label)
                elif choice.isdigit():  # pragma: no branch
                    LOGGER.debug("User selected url %s", choice)
                    success = self.open(url_list[int(choice) - 1])
                    if success:
                        self.opened_entries.add(label)

        Event.PostOpenCommand.fire(self)

    @staticmethod
    def open(url: ParseResult) -> bool:
        """Opens a URL, ensuring we can deal with a program taking over the terminal to do so.

        Args:
            url: the URL to be opened.

        Returns:
            Whether `url` was opened successfully.
        """
        app = get_active_app()
        if app is None:
            return OpenCommand._open_url(url)
        # NOTE: we are unable to test this in CI at this time, because the textual Pilot interface
        # does not support suspend.
        with app.suspend():
            return OpenCommand._open_url(url)

    @staticmethod
    def _open_url(url: ParseResult) -> bool:
        """Opens a URL.

        Args:
            url: the URL to be opened.

        Returns:
            Whether `url` was opened successfully.
        """
        opener = config.commands.open.command
        success = False
        try:
            url_str = url.geturl()
            if not url.scheme:
                url_path = RelPath(url_str)
                if not url_path.path.exists():
                    raise FileNotFoundError(f"Could not find the file at '{url_path.path}'!")
                url_str = str(url_path.path)
            LOGGER.debug('Opening "%s" with %s.', url_str, opener)
            os.system(f"{opener} {url_str}")
            success = True

        except FileNotFoundError as err:
            LOGGER.error(err)

        return success

    @staticmethod
    def _wrap_prompt_process_response(
        func: Callable[[PromptBase[PromptType], str], PromptType],
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
