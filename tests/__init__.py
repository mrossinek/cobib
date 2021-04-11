"""coBib's test suite."""

from pathlib import Path, PurePath

from .cmdline_test import CmdLineTest


def get_resource(filename: str, path: str = None) -> str:
    """Gets the absolute path of the filename."""
    root = Path(__file__).parent
    full_path = root if path is None else root / Path(path)
    return str(full_path / filename)


def get_path_relative_to_home(path: str) -> str:
    """Returns the path relative to the user's home directory."""
    home = Path(path).home()
    try:
        return str("~" / PurePath(path).relative_to(home))
    except ValueError:
        # TODO: leverage `PurePath.is_relative_to(home)` when Python 3.9 becomes the default
        return path
