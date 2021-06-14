"""coBib's debugging config."""

from pathlib import Path

from cobib.config import config

root = Path(__file__).parent
config.database.file = str((root / "example_literature.yaml").resolve())

config.utils.journal_abbreviations = [
    ("Annalen der Physik", "Ann. Phys."),
]
