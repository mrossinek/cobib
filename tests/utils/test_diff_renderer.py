"""Tests for coBib's diff renderer utility."""

from rich.syntax import Syntax
from rich.table import Table

from cobib.utils.diff_renderer import Differ

# pylint: disable=line-too-long
LEFT = """@article{Cao2018,
  archivePrefix = {arXiv},
  arxivid = {1812.09976v2},
  author = {Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and Peter D. Johnson and M{\'a}ria Kieferov{\'a} and Ian D. Kivlichan and Tim Menke and Borja Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and Al{\'a}n Aspuru-Guzik},
  doi = {10.1021/acs.chemrev.8b00803},
  eprint = {http://arxiv.org/abs/1812.09976v2},
  primaryClass = {quant-ph},
  title = {Quantum Chemistry in the Age of Quantum Computing},
  url = {http://dx.doi.org/10.1021/acs.chemrev.8b00803},
  year = {2018}
}"""

# pylint: disable=line-too-long
RIGHT = """@article{Cao_2019,
  author = {Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and Peter D. Johnson and M{\'a}ria Kieferov{\'a} and Ian D. Kivlichan and Tim Menke and Borja Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and Al{\'a}n Aspuru-Guzik},
  doi = {10.1021/acs.chemrev.8b00803},
  journal = {Chemical Reviews},
  month = {8},
  number = {19},
  pages = {10856--10915},
  publisher = {American Chemical Society ({ACS})},
  title = {Quantum Chemistry in the Age of Quantum Computing},
  url = {https://doi.org/10.1021%2Facs.chemrev.8b00803},
  volume = {119},
  year = {2019}
}"""


def test_differ() -> None:
    """Test initialization a Differ object."""
    differ = Differ(LEFT, RIGHT)
    differ.compute()
    table = differ.render("bibtex")
    assert isinstance(table, Table)
    assert isinstance(list(table.columns[0].cells)[0], Syntax)
    assert isinstance(list(table.columns[1].cells)[0], Syntax)
