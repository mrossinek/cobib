#!/usr/bin/env python3
"""coBib main body."""

import asyncio
import sys

from cobib.ui.cli import CLI
from cobib.ui.shell_helper import ShellHelper


async def main() -> None:
    """Main executable.

    coBib's main function used to parse optional keyword arguments and subcommands.
    """
    if len(sys.argv) > 1 and any(a[0] == "_" for a in sys.argv):
        # shell helper function called
        ShellHelper()
    else:
        await CLI().run()


if __name__ == "__main__":
    asyncio.run(main())  # pragma: no cover
