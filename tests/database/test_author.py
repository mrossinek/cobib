"""Tests for coBib's Author class."""

from __future__ import annotations

import pytest

from cobib.database import Author


@pytest.mark.parametrize(
    ["string", "expected", "formatted"],
    [
        # Test cases taken from https://www.bibtex.com/f/author-field/
        ["Michael Joseph Jackson", Author("Michael Joseph", "Jackson"), "Jackson, Michael Joseph"],
        ["Jackson, Michael Joseph", Author("Michael Joseph", "Jackson"), "Jackson, Michael Joseph"],
        ["Jackson, Michael J", Author("Michael J", "Jackson"), "Jackson, Michael J"],
        ["Jackson, M J", Author("M J", "Jackson"), "Jackson, M J"],
        [
            "Stoner, Jr, Winifred Sackville",
            Author("Winifred Sackville", "Stoner", suffix="Jr"),
            "Stoner, Jr, Winifred Sackville",
        ],
        [
            "Ludwig van Beethoven",
            Author("Ludwig", "Beethoven", particle="van"),
            "van Beethoven, Ludwig",
        ],
        [
            "van Beethoven, Ludwig",
            Author("Ludwig", "Beethoven", particle="van"),
            "van Beethoven, Ludwig",
        ],
        ["van Beethoven, L", Author("L", "Beethoven", particle="van"), "van Beethoven, L"],
        ["{Barnes and Noble, Inc.}", "{Barnes and Noble, Inc.}", "{Barnes and Noble, Inc.}"],
        ["{FCC H2020 Project}", "{FCC H2020 Project}", "{FCC H2020 Project}"],
        [
            "von Mustermann, Jr, Max",
            Author("Max", "Mustermann", "von", "Jr"),
            "von Mustermann, Jr, Max",
        ],
        [
            "Double Surname, Many First Names",
            Author("Many First Names", "Double Surname"),
            "Double Surname, Many First Names",
        ],
    ],
)
def test_author_parsing(string: str, expected: str | Author, formatted: str) -> None:
    """Tests the `Author.parse` method."""
    output = Author.parse(string)
    assert output == expected
    assert str(output) == formatted


def test_author_parsing_error() -> None:
    """Tests that `Author.parse` raises an error with two many commas."""
    with pytest.raises(ValueError):
        Author.parse("string, with, three, commas")
