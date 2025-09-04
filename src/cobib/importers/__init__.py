"""coBib's importers.

.. include:: ../man/cobib-importers.7.html_fragment

coBib provides various "importers" which handle the migration from other bibliography managers.
The abstract interface which should be implemented is defined in `cobib.importers.base_importer`.
"""

from .bibtex import BibtexImporter as BibtexImporter
from .zotero import ZoteroImporter as ZoteroImporter
