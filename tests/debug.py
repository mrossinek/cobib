"""coBib's debugging config."""

from pathlib import Path

from cobib.config import config

config.logging.version = None

root = Path(__file__).parent
config.database.file = str((root / "example_literature.yaml").resolve())

config.utils.file_downloader.url_map[
    r"(.+)://quantum-journal.org/papers/([^/]+)"
] = r"\1://quantum-journal.org/papers/\2/pdf/"

config.utils.journal_abbreviations = [
    ("Annalen der Physik", "Ann. Phys."),
]
