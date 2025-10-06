"""coBib exporter test class."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile

import pytest

from cobib.config import config
from cobib.database import Database

from .. import get_resource

TMPDIR = Path(tempfile.gettempdir()).resolve()


class ExporterTest:
    """The base class for coBib's exporter test classes."""

    COBIB_TEST_DIR = TMPDIR / "cobib_test"
    """Path to the temporary coBib test directory."""

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        """Setup."""
        config.defaults()
        config.database.file = self.COBIB_TEST_DIR / "database.yaml"

        self.COBIB_TEST_DIR.mkdir(parents=True, exist_ok=True)
        copyfile(get_resource("example_literature.yaml"), config.database.file)
        Database().read()

        yield

        # clean up file system
        Path(config.database.file).unlink(missing_ok=True)

        # clean up database
        Database.reset()

        # ensure that we also clean up whatever we have set up
        config.defaults()
