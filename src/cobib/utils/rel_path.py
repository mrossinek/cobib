"""coBib's path utility."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

XDG_BASE_DIRS: dict[str, str] = {
    "XDG_CONFIG_HOME": os.getenv("XDG_CONFIG_HOME", "$HOME/.config"),
    "XDG_CACHE_HOME": os.getenv("XDG_CACHE_HOME", "$HOME/.cache"),
    "XDG_DATA_HOME": os.getenv("XDG_DATA_HOME", "$HOME/.local/share"),
    "XDG_STATE_HOME": os.getenv("XDG_STATE_HOME", "$HOME/.local/state"),
}
"""A dictionary of XDG base directory paths.

For more details see [here](https://wiki.archlinux.org/title/XDG_Base_Directory).
"""

for key, val in XDG_BASE_DIRS.items():
    if key not in os.environ:
        os.environ[key] = os.path.expandvars(val)


class RelPath:
    """The RelPath object.

    This object is a simple wrapper of a `pathlib.Path` object which ensures that a path is, if
    possible, relative to the user's home directory or an absolute path.
    This path does *not* get expanded when converting the object to a `str`, which happens during
    storage in the database.
    *Only* when accessing other attributes, will they be forwarded to a `pathlib.Path` instance of
    the fully-resolved, absolute path.
    """

    HOME = Path.home()
    """The path of the user's home directory."""

    def __init__(self, path: str | Path) -> None:
        """Initializes the path.

        This will first expand and fully resolve the given path and store it internally as a path
        relative to the user's home directory (if possible) or as an absolute path.

        Args:
            path: the path to store.
        """
        full_path = Path(os.path.expandvars(path)).expanduser().resolve()
        try:
            self._path = "~" / full_path.relative_to(self.HOME)
        except ValueError:
            self._path = full_path

    def __getattr__(self, attr: str) -> Any:
        """Gets an attribute from the internal path.

        Args:
            attr: the attribute to get.

        Returns:
            The attribute's value.
        """
        return getattr(self.path, attr)

    def __str__(self) -> str:
        """Transforms the internal path to a string.

        This is the only method which will not automatically expand the internal path to its
        fully-resolved, absolute version.
        """
        return str(self._path)

    @property
    def path(self) -> Path:
        """The fully-resolved, absolute path."""
        return self._path.expanduser().resolve()
