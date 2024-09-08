"""Tests for coBib's diff renderer utility."""

from rich.syntax import Syntax
from rich.table import Table

from cobib.utils.diff_renderer import Differ

LEFT = """@article{Rossmannek2023,
  archivePrefix = {arXiv},
  arxivid = {2302.03052},
  author = {Rossmannek, Max and Pavo{\v s}evi{\'c}, Fabijan and Rubio, Angel and Tavernelli, Ivano},
  doi = {10.1021/acs.jpclett.3c00330},
  eprint = {http://arxiv.org/abs/2302.03052},
  primaryClass = {physics.chem-ph},
  title = {Quantum embedding method for the simulation of strongly correlated systems on quantum computers},
  url = {http://dx.doi.org/10.1021/acs.jpclett.3c00330},
  year = {2023}
}"""  # noqa: E501


RIGHT = """@article{Rossmannek_2023,
  author = {Rossmannek, Max and Pavo{\v{s}}evi{\'c}, Fabijan and Rubio, Angel and Tavernelli, Ivano},
  doi = {10.1021/acs.jpclett.3c00330},
  journal = {The Journal of Physical Chemistry Letters},
  month = {4},
  number = {14},
  pages = {3491--3497},
  publisher = {American Chemical Society ({ACS})},
  title = {Quantum Embedding Method for the Simulation of Strongly Correlated Systems on Quantum Computers},
  url = {https://doi.org/10.1021%2Facs.jpclett.3c00330},
  volume = {14},
  year = {2023}
}"""  # noqa: E501


def test_differ() -> None:
    """Test initialization a Differ object."""
    differ = Differ(LEFT, RIGHT)
    differ.compute()
    table = differ.render("bibtex")
    assert isinstance(table, Table)
    assert isinstance(next(iter(table.columns[0].cells)), Syntax)
    assert isinstance(next(iter(table.columns[1].cells)), Syntax)
