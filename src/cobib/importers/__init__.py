"""coBib's importers.

coBib provides various "importers" which handle the migration from other bibliography managers.
The abstract interface which should be implemented is defined in `cobib.importers.base_importer`.
"""

from .zotero import ZoteroImporter as ZoteroImporter
