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

from pathlib import Path, PurePath
from typing import List, Optional

from .cmdline_test import CmdLineTest


def get_resource(filename: str, path: Optional[str] = None) -> str:
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

    # pylint: disable=missing-function-docstring

    def __init__(self, string: Optional[List[str]] = None) -> None:
        # noqa: D107
        if string is None:
            string = []
        self.string = string + ["\n"]

    def readline(self) -> str:
        # noqa: D102
        return self.string.pop(0)
