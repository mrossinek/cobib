"""coBib's test suite."""

from pathlib import Path, PurePath
from typing import Optional

from .cmdline_test import CmdLineTest


def get_resource(filename: str, path: Optional[str] = None) -> str:
    """Gets the absolute path of the filename."""
    root = Path(__file__).parent
    full_path = root if path is None else root / Path(path)
    return str(full_path / filename)
