"""coBib parser test class."""

from .. import get_resource


class ParserTest:
    """The base class for coBib's parser test classes."""

    EXAMPLE_BIBTEX_FILE = get_resource("example_entry.bib")

    EXAMPLE_YAML_FILE = get_resource("example_entry.yaml")

    EXAMPLE_ENTRY_DICT = {
        "ENTRYTYPE": "article",
        "author": "Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and "
        + "Peter D. Johnson and M{\\'a}ria Kieferov{\\'a} and Ian D. Kivlichan and Tim Menke and "
        + "Borja Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and Al{\\'a}n "
        + "Aspuru-Guzik",
        "doi": "10.1021/acs.chemrev.8b00803",
        "journal": "Chemical Reviews",
        "month": "aug",
        "number": 19,
        "pages": "10856--10915",
        "publisher": "American Chemical Society ({ACS})",
        "title": "Quantum Chemistry in the Age of Quantum Computing",
        "url": ["https://doi.org/10.1021%2Facs.chemrev.8b00803"],
        "volume": 119,
        "year": 2019,
    }