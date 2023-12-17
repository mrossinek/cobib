"""coBib's Journal abbreviations."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import ClassVar

from cobib.config import config

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class JournalAbbreviations:
    """The Journal abbreviation singleton.

    This utility centralizes coBib's methodology of converting between full and abbreviated journal
    names. It implements the singleton pattern to enforce consistency across all modules.
    """

    _instance: JournalAbbreviations | None = None
    """The singleton instance of this class."""

    _abbreviations: ClassVar[dict[str, str]] = {}
    """The parsed abbreviations."""

    _fullwords: ClassVar[dict[str, str]] = {}
    """The inverted, parsed abbreviations."""

    def __new__(cls) -> JournalAbbreviations:
        """Singleton constructor.

        This method gets called when accessing `JournalAbbreviations` and enforces the singleton
        pattern implemented by this class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def load_abbreviations() -> None:
        """Load the list of abbreviations from the user configuration.

        By default, coBib does not ship with any abbreviations. Instead, the user is required to
        provide his own list via `config.utils.journal_abbreviations`. This setting must be a list
        of tuples formatted as: `("full name", "abbreviation")`.
        """
        for fullword, abbreviation in config.utils.journal_abbreviations:
            JournalAbbreviations._abbreviations[fullword] = abbreviation
            JournalAbbreviations._fullwords[abbreviation] = fullword
            JournalAbbreviations._fullwords[abbreviation.replace(".", "")] = fullword

    @staticmethod
    def check_existence(journal: str) -> bool:
        """Checks whether a journal name is present in the user's configuration.

        Args:
            journal: the journal name to check for.

        Returns:
            A boolean indicating whether this journal name is configured.
        """
        if not JournalAbbreviations._abbreviations:
            JournalAbbreviations.load_abbreviations()

        if journal in JournalAbbreviations._abbreviations:
            return True
        if journal in JournalAbbreviations._fullwords:
            return True

        msg = (
            f"'{journal}' was not found in your list of journal abbreviations! If you want to be "
            "able to automatically convert between full journal names and their abbreviated "
            "versions, consider adding a tuple like '(full journal name, abbreviation)' to the list"
            " stored under config.utils.journal_abbreviations"
        )
        LOGGER.warning(msg)
        return False

    @staticmethod
    def abbreviate(journal: str, dotless: bool = False) -> str:
        """Abbreviates the given journal name.

        Args:
            journal: the journal name to abbreviate.
            dotless: whether to return the abbreviated name without punctuation.

        Returns:
            The abbreviated journal name. If the provided journal name has no configured
            abbreviation, it will be returned unchanged. The `dotless` argument will have *no*
            effect!
        """
        if not JournalAbbreviations.check_existence(journal):
            return journal

        remove_punctuation: Callable[[str], str] = (  # noqa: E731
            lambda journal: journal.replace(".", "") if dotless else journal
        )

        if journal in JournalAbbreviations._fullwords:
            LOGGER.debug("'%s' is already abbreviated.", journal)
            return remove_punctuation(journal)

        new_journal = JournalAbbreviations._abbreviations.get(journal, journal)

        return remove_punctuation(new_journal)

    @staticmethod
    def elongate(journal: str) -> str:
        """Elongates the given journal name.

        Args:
            journal: the journal name to elongate.

        Returns:
            The elongated journal name. If the provided journal name has no configured elongation,
            it will be returned unchanged.
        """
        if not JournalAbbreviations.check_existence(journal):
            return journal

        if journal in JournalAbbreviations._abbreviations:
            LOGGER.info("'%s' is already elongated.", journal)
            return journal

        new_journal = JournalAbbreviations._fullwords.get(journal, journal)
        return new_journal
