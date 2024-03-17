"""A cobib configuration file for this test suite."""

from pathlib import Path

from cobib.config import config

config.logging.version = None

root = Path(__file__).parent
config.database.cache = None
config.database.file = str((root / "testing.yaml").resolve())
