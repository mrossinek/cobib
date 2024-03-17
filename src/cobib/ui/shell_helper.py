"""coBib's shell helper interface.

This class provides access to the commands implemented in the `cobib.utils.shell_helper` module.
A user can access those from the command-line by prefixing the various function names of that module
with an underscore, for example: `cobib _example_config`.

This entire module is deprecated and will be removed in version 5.0 of coBib.
"""

import argparse
import inspect
import logging
from typing import Any

from typing_extensions import override

from cobib.ui.ui import UI
from cobib.utils import shell_helper

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ShellHelper(UI):
    """The shell-helper interface class.

    In addition to the global arguments documented by the base class, the following are supported:

      * `helper`: a single position argument indicating the name of the shell-helper utility
        function to run (prefixed with a single underscore, for example `_example_config`).
    """

    @override
    def add_extra_parser_arguments(self) -> None:
        available_helpers = [
            "_" + m[0] for m in inspect.getmembers(shell_helper) if inspect.isfunction(m[1])
        ]
        self.parser.add_argument(
            "helper", help="shell helper to be called", choices=available_helpers
        )
        self.parser.add_argument("args", nargs=argparse.REMAINDER)

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()

        self.init_argument_parser(description="Process shell helper call")

    @override
    def run(self) -> None:
        arguments = self.parse_args()

        helper = getattr(shell_helper, arguments.helper.strip("_"))
        # any shell helper function will return a list of the requested items
        for item in helper(*arguments.args):
            print(item)
