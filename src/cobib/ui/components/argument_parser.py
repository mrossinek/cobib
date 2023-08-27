"""coBib's ArgumentParser.

This is merely a simple wrapper around the builtin `argparse.ArgumentParser` in order to bring the
[`exit_on_error`](https://docs.python.org/3/library/argparse.html#exit-on-error) behavior to Python
versions lower than 3.9.

.. warning::

   Since this is merely a utility to support Python 3.8, once support for that will be dropped, this
   class will be removed without further notice.
"""

from __future__ import annotations

import argparse
from typing import NoReturn


class ArgumentParser(argparse.ArgumentParser):
    """Wrapper of the `argparse.ArgumentParser` to allow catching of error messages.

    Note, this class will be removed once Python 3.9 becomes the minimal supported version as it
    added the [`exit_on_error`](https://docs.python.org/3/library/argparse.html#exit-on-error)
    keyword argument.
    """

    # TODO: once Python 3.9 becomes the default, make use of the exit_on_error argument.

    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        """Overwrite the exit method to raise an error rather than exit.

        Args:
            status: the status code. If non-zero, an `argparse.ArgumentError` will be raised.
            message: the message of the error.

        Raises:
            An `argparse.ArgumentError`.
        """
        if status:
            raise argparse.ArgumentError(None, f"Error: {message}")
        super().exit(status, message)  # pragma: no cover
