"""Read one of coBib's man pages.

.. include:: ../man/cobib-man.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging

from rich.console import ConsoleRenderable
from rich.markdown import Markdown
from typing_extensions import override

from cobib.config import Event
from cobib.man import manual

from .base_command import Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ManCommand(Command):
    """The Man Command.

    This command can parse the following arguments:

        * `page`: an optional name of the man-page to view. If this argument is omitted, an index of
            all registered man-pages will be printed instead.
    """

    name = "man"

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.contents: str | None = None
        """The text content of the man-page to be viewed. When no `page` argument was supplied, this
        is `None` resulting in an index of all registered man-pages being returned by this command.
        """

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="man",
            description="Man subcommand parser.",
            epilog="Read cobib-man.1 and cobib-man.7 for more help.",
        )
        parser.add_argument(
            "page", type=str, nargs="?", default=None, help="The name of the man-page to view"
        )
        cls.argparser = parser

    @override
    def execute(self) -> None:
        LOGGER.debug("Starting Man command.")

        Event.PreManCommand.fire(self)

        if self.largs.page is None:
            self.contents = None

        else:
            self.largs.page = manual.resolve_name(self.largs.page)
            path = manual.path_from_name(self.largs.page)

            with open(path) as manpage:
                self.contents = manpage.read()

        Event.PostManCommand.fire(self)

    @override
    def render_porcelain(self) -> list[str]:
        if self.contents is None:
            return manual.render_porcelain()

        return self.contents.split("\n")

    @override
    def render_rich(self) -> ConsoleRenderable:
        if self.contents is None:
            return manual.render_rich()

        return Markdown(self.contents)
