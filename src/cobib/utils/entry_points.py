"""coBib's `entry_points` method.

This is merely a simple wrapper around the builtin `importlib.metadata.entry_points` method in order
to bring the ["selectable"](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
behavior to Python versions lower than 3.10.
While this would theoretically be possible via the `backports.entry_points_selectable` package, that
does not also add the `module` attributes to the `EntryPoint` objects which this method also allows
to filter by.

.. warning::

   Since this is merely a utility to support Python < 3.10, once support for that will be dropped,
   this method will be removed without further notice.
"""

from __future__ import annotations

import sys
from importlib.metadata import EntryPoint
from importlib.metadata import entry_points as _entry_points


def entry_points(filter: str) -> set[tuple[EntryPoint, bool]]:
    """A wrapper of `importlib.metadata.entry_points`.

    This method extracts the group of entry points matching the `filter` by name. It will also
    indicate whether each entry point actually comes directly from the module of the same name.

    .. note::
       This method returns a set (rather than the normal list or tuple) to avoid duplicate entries
       which would sometimes appear in lower Python versions during some initial testing.

    Args:
        filter: the name of the group and module to check for.

    Returns:
        The filtered set of `EntryPoint` objects wrapped into a tuple with the second element
        indicating whether it belongs to the queried module.
    """
    if sys.version_info.minor > 9:  # noqa: PLR2004
        return {
            (cls, cls.module.startswith(filter))  # type: ignore[attr-defined,misc]
            for cls in _entry_points(group=filter)  # type: ignore[call-arg]
        }
    return {  # pragma: no cover
        (cls, cls.value.startswith(filter)) for cls in _entry_points()[filter]
    }
