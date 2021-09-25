"""coBib's parsers.

coBib provides a variety of parsers which handle the translation from (and to) specific sources into
`cobib.database.Entry` instances.
The abstract interface which should be implemented is defined by the `cobib.parsers.base_parser`.
"""

from .arxiv import ArxivParser as ArxivParser
from .bibtex import BibtexParser as BibtexParser
from .doi import DOIParser as DOIParser
from .isbn import ISBNParser as ISBNParser
from .url import URLParser as URLParser
from .yaml import YAMLParser as YAMLParser
