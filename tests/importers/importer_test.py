"""coBib importer test class."""

from collections.abc import Generator

import pytest

from cobib.config import config


class ImporterTest:
    """The base class for coBib's importer test classes."""

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        """Setup."""
        config.defaults()

        yield

        # ensure that we also clean up whatever we have set up
        config.defaults()
