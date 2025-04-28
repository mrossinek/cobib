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
except ModuleNotFoundError:  # pragma: no cover
    # NOTE: we ignore coverage below because the CI has an additional job running the unittests
    # without optional dependencies available.
    LOGGER.info(  # pragma: no cover
        "Could not find the `regex` package. Falling back to the builtin `re` module. Certain "
        "functionality may not be available without the optional `regex` dependency installed."
    )
    import re as regex  # type: ignore[no-redef]  # pragma: no cover
else:
    HAS_OPTIONAL_REGEX = True
    LOGGER.info("Found the `regex` package.")

__all__ = ["HAS_OPTIONAL_REGEX", "regex"]
