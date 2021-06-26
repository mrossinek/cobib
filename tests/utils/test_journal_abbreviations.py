"""Tests for coBib's Journal abbreviations."""
# pylint: disable=protected-access

from typing import Any, Generator

import pytest

from cobib.config import config
from cobib.utils.journal_abbreviations import JournalAbbreviations


@pytest.fixture(autouse=True)
def setup() -> Generator[Any, None, None]:
    """Setup.

    This method is mostly used to reset the JournalAbbreviations to their original state.

    Yields:
        Access to the local fixture variables.
    """
    yield
    config.utils.journal_abbreviations = []
    JournalAbbreviations._abbreviations = {}
    JournalAbbreviations._fullwords = {}


def test_downloader_singleton() -> None:
    """Test the JournalAbbreviations is a Singleton."""
    j_a = JournalAbbreviations()
    j_a2 = JournalAbbreviations()
    assert j_a is j_a2


def test_load_abbreviations() -> None:
    """Test the JournalAbbreviations.load_abbreviations method."""
    config.utils.journal_abbreviations = [("Test Journal", "Test J.")]
    JournalAbbreviations.load_abbreviations()
    assert JournalAbbreviations._abbreviations == {"Test Journal": "Test J."}
    assert JournalAbbreviations._fullwords == {"Test J.": "Test Journal", "Test J": "Test Journal"}


def test_check_existence(caplog: pytest.LogCaptureFixture) -> None:
    """Test the JournalAbbreviations.check_existence method.

    Args:
        caplog: the built-in pytest fixture.
    """
    assert JournalAbbreviations.check_existence("Test Journal") is False
    for scope, level, message in caplog.record_tuples:
        if (
            scope == "cobib.utils.journal_abbreviations"
            and level == 30
            and "'Test Journal' was not found" in message
        ):
            break
    else:
        assert False, "Warning not raised upon missing journal!"
    caplog.clear()
    config.utils.journal_abbreviations = [("Test Journal", "Test J.")]
    assert JournalAbbreviations.check_existence("Test Journal")
    assert JournalAbbreviations.check_existence("Test J.")
    assert JournalAbbreviations.check_existence("Test J")


@pytest.mark.parametrize("dotless", [False, True])
def test_abbreviate(dotless: bool) -> None:
    """Test the JournalAbbreviations.abbreviate method.

    Args:
        dotless: whether to abbreviate with or without punctuation.
    """
    old_journal = "Test Journal"
    new_journal = JournalAbbreviations.abbreviate(old_journal, dotless=dotless)
    assert new_journal == old_journal
    config.utils.journal_abbreviations = [("Test Journal", "Test J.")]
    new_journal = JournalAbbreviations.abbreviate(old_journal, dotless=dotless)
    expected = "Test J" if dotless else "Test J."
    assert new_journal == expected


def test_elongate() -> None:
    """Test the JournalAbbreviations.elongate method."""
    old_journal = "Test J."
    new_journal = JournalAbbreviations.elongate(old_journal)
    assert new_journal == old_journal
    config.utils.journal_abbreviations = [("Test Journal", "Test J.")]
    new_journal = JournalAbbreviations.elongate(old_journal)
    assert new_journal == "Test Journal"
    old_journal = "Test Journal"
    new_journal = JournalAbbreviations.elongate(old_journal)
    assert new_journal == "Test Journal"
