"""TODO."""

import argparse
from typing import NoReturn, Optional


class ArgumentParser(argparse.ArgumentParser):
    """Wrapper of the `argparse.ArgumentParser` to allow catching of error messages.

    Note, this class will be removed once Python 3.9 becomes the minimal supported version as it
    added the [`exit_on_error`](https://docs.python.org/3/library/argparse.html#exit-on-error)
    keyword argument.
    """

    # TODO: once Python 3.9 becomes the default, make use of the exit_on_error argument.

    def exit(self, status: int = 0, message: Optional[str] = None) -> NoReturn:
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
