"""coBib's parsers.

coBib provides a variety of parsers which handle the translation from (and to) specific sources into
`cobib.database.Entry` instances.
The abstract interface which should be implemented is defined by the `cobib.parsers.base_parser`.
"""

from .arxiv import ArxivParser
from .bibtex import BibtexParser
from .doi import DOIParser
from .isbn import ISBNParser
from .yaml import YAMLParser
