"""coBib's manual.

.. include:: cobib.1.html_fragment
"""

from pathlib import Path

from .manual import manual as manual

TUTORIAL_IMPORT_DATABASE = Path(__file__).parent / "top10.bib"
"""Path to the BibTeX database used with `import` during the guided `cobib.commands.tutorial`."""

TUTORIAL_ADD_ENTRY = Path(__file__).parent / "top10_ref.bib"
"""Path to the single BibTeX entry used with `add` during the guided `cobib.commands.tutorial`."""

TUTORIAL_ADD_FILE = Path(__file__).parent / "Van_Noorden_2014.txt"
"""Path to the basic file attachment used with `add` during the guided `cobib.commands.tutorial`."""
