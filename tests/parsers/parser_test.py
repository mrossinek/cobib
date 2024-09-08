"""coBib parser test class."""

from __future__ import annotations

from typing import Any, ClassVar

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

    EXAMPLE_ENTRY_DICT: ClassVar[dict[str, Any]] = {
        "ENTRYTYPE": "article",
        "author": [
            Author(first="Max", last="Rossmannek"),
            Author(first="Fabijan", last="Pavošević"),
            Author(first="Angel", last="Rubio"),
            Author(first="Ivano", last="Tavernelli"),
        ],
        "doi": "10.1021/acs.jpclett.3c00330",
        "issn": "1948-7185",
        "journal": "The Journal of Physical Chemistry Letters",
        "month": "apr",
        "number": 14,
        "pages": "3491–3497",  # noqa: RUF001
        "publisher": "American Chemical Society (ACS)",
        "title": (
            "Quantum Embedding Method for the Simulation of Strongly Correlated Systems on Quantum "
            "Computers"
        ),
        "url": ["http://dx.doi.org/10.1021/acs.jpclett.3c00330"],
        "volume": 14,
        "year": 2023,
    }
    """The matching dictionary to the example files also included here."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Setup."""
        config.defaults()
