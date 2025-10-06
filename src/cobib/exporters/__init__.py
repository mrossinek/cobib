"""coBib's exporters.

.. include:: ../man/cobib-exporters.7.html_fragment

coBib provides various "exporters" which handle the process of dumping database contents in
different formats.
The abstract interface which should be implemented is defined in `cobib.exporters.base_exporter`.
"""

from .bibtex import BibtexExporter as BibtexExporter
from .zip import ZipExporter as ZipExporter
