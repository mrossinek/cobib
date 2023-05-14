"""TODO."""

import argparse
import inspect
import logging

from cobib.ui.ui import UI
from cobib.utils import shell_helper

LOGGER = logging.getLogger(__name__)


class ShellHelper(UI):
    """TODO."""

    def add_extra_parser_arguments(self) -> None:
        """TODO."""
        available_helpers = [
            "_" + m[0] for m in inspect.getmembers(shell_helper) if inspect.isfunction(m[1])
        ]
        self.parser.add_argument(
            "helper", help="shell helper to be called", choices=available_helpers
        )
        self.parser.add_argument("args", nargs=argparse.REMAINDER)

    def __init__(self) -> None:
        """TODO."""
        super().__init__()

        self.init_argument_parser(description="Process shell helper call")

        arguments = self.parse_args()

        helper = getattr(shell_helper, arguments.helper.strip("_"))
        # any shell helper function will return a list of the requested items
        for item in helper(*arguments.args):
            print(item)
