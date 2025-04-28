#!/usr/bin/env python3
"""coBib main body."""

import asyncio

from cobib.ui.cli import CLI


async def main() -> None:
    """Main async executable.

    coBib's main function used to parse optional keyword arguments and subcommands.
    """
    await CLI().run()


def _main() -> None:
    """The main method wrapping the async method with `asyncio.run`."""
    asyncio.run(main())  # pragma: no cover


if __name__ == "__main__":
    _main()  # pragma: no cover
