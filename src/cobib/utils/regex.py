"""coBib's wrapper around the `re` and `regex` packages.

Since `regex` is an optional dependency that can be used as a drop-in replacement of the builtin
`re` module, this simple module deals with exposing either one.
"""

from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)

HAS_OPTIONAL_REGEX = False

try:
    import regex
except ModuleNotFoundError:
    LOGGER.info(
        "Could not find the `regex` package. Falling back to the builtin `re` module. Certain "
        "functionality may not be available without the optional `regex` dependency installed."
    )
    import re as regex  # type: ignore[no-redef]
else:
    HAS_OPTIONAL_REGEX = True
    LOGGER.info("Found the `regex` package.")

__all__ = ["regex", "HAS_OPTIONAL_REGEX"]
