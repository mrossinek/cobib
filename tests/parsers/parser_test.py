"""coBib parser test class."""

import pytest

from cobib.config import config
from cobib.database import Author

from .. import get_resource


class ParserTest:
    """The base class for coBib's parser test classes."""

    EXAMPLE_BIBTEX_FILE = get_resource("example_entry.bib")
    """Path to the example BibTeX file."""

    EXAMPLE_YAML_FILE = get_resource("example_entry.yaml")
    """Path to the example YAML file (matching the BibTeX file)."""

    EXAMPLE_ENTRY_DICT = {
        "ENTRYTYPE": "article",
        "author": [
            Author(first="Yudong", last="Cao"),
            Author(first="Jonathan", last="Romero"),
            Author(first="Jonathan P.", last="Olson"),
            Author(first="Matthias", last="Degroote"),
            Author(first="Peter D.", last="Johnson"),
            Author(first="Mária", last="Kieferová"),
            Author(first="Ian D.", last="Kivlichan"),
            Author(first="Tim", last="Menke"),
            Author(first="Borja", last="Peropadre"),
            Author(first="Nicolas P. D.", last="Sawaya"),
            Author(first="Sukin", last="Sim"),
            Author(first="Libor", last="Veis"),
            Author(first="Alán", last="Aspuru-Guzik"),
        ],
        "doi": "10.1021/acs.chemrev.8b00803",
        "issn": "1520-6890",
        "journal": "Chemical Reviews",
        "month": "aug",
        "number": 19,
        "pages": "10856–10915",
        "publisher": "American Chemical Society (ACS)",
        "title": "Quantum Chemistry in the Age of Quantum Computing",
        "url": ["http://dx.doi.org/10.1021/acs.chemrev.8b00803"],
        "volume": 119,
        "year": 2019,
    }
    """The matching dictionary to the example files also included here."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Setup."""
        config.defaults()
