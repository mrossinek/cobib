"""coBib's Test Suite.

The test suite is organized into submodules which mirror the layout of the source code. As such,
each file in the source should have a corresponding file with unittests.
In most cases, the unittests will be organized into classes which derive from a common base test
class at the submodule level.

To run the test suite with coverage reporting, use:
```
tox -e coverage
```
For quick testing of individual files, it is easier to use:
```
pytest <path/to/test/file.py>
```
Check out `pytest --help` for more options.
"""

from __future__ import annotations

from io import UnsupportedOperation
from pathlib import Path


def get_resource(filename: str, path: str | None = None) -> str:
    """A utility method to get the absolute path to a resource in the test suite.

    Args:
        filename: the name of the file to get.
        path: an optional path relative to the root of the test suite.

    Returns:
        The absolute path of the file.
    """
    root = Path(__file__).parent
    full_path = root if path is None else root / Path(path)
    return str(full_path / filename)


class MockStdin:
    """A mock object to replace `sys.stdin`."""

    def __init__(self, string: list[str] | None = None) -> None:
        """Initializes a fake standard input.

        Arsg:
            string: an optional list of strings to type as the fake input.
        """
        if string is None:
            string = []
        self.string = [*string, "\n"]

    def fileno(self) -> None:
        """A dummy fileno method raising an appropriate error for `prompt_toolkit` to detect."""
        raise UnsupportedOperation

    def readline(self) -> str:
        """Fakes reading a line.

        Returns:
            The read line.
        """
        return self.string.pop(0)
