"""coBib importer test class."""

import pytest

from cobib.config import config


class ImporterTest:
    """The base class for coBib's importer test classes."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        # pylint: disable=no-self-use
        """Setup."""
        config.defaults()
