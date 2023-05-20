#!/usr/bin/env python3
"""coBib main body."""

import asyncio
import sys

from cobib.ui.cli import CLI
from cobib.ui.shell_helper import ShellHelper


async def main() -> None:
    """Main async executable.

    coBib's main function used to parse optional keyword arguments and subcommands.
    """
    if len(sys.argv) > 1 and any(a[0] == "_" for a in sys.argv):
        # shell helper function called
        ShellHelper().run()
    else:
        await CLI().run()


def _main() -> None:
    """The main method wrapping the async method with `asyncio.run`."""
    asyncio.run(main())


if __name__ == "__main__":
    _main()  # pragma: no cover
