"""Tests for coBib's manual indexer."""

from __future__ import annotations

from pathlib import Path

import pytest

import cobib.man
from cobib.man import manual

COBIB_MAN_PATH = Path(cobib.man.__file__).parent


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("cobib", "cobib.1"),
        ("cobib.1", "cobib.1"),
        ("cobib(1)", "cobib.1"),
        ("git", "cobib-git.1"),
        ("git.7", "cobib-git.7"),
        ("config", "cobib-config.5"),
        ("start", "cobib-getting-started.7"),
        ("missing", None),
    ],
)
def test_resolve_name(input: str, expected: str | None) -> None:
    """Test the Manual.resolve_name method.

    Args:
        input: the input string.
        expected: the expected output. If `None`, a `KeyError` should get raised.
    """
    if expected is None:
        with pytest.raises(KeyError):
            manual.resolve_name(input)
    else:
        assert expected == manual.resolve_name(input)


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("cobib.1", COBIB_MAN_PATH / "cobib.1.md"),
        ("cobib-config.5", COBIB_MAN_PATH / "cobib-config.5.md"),
        ("cobib-missing.1", None),
    ],
)
def test_path_from_name(input: str, expected: Path | None) -> None:
    """Test the Manual.path_from_name method.

    Args:
        input: the input string.
        expected: the expected output. If `None`, a `KeyError` should get raised.
    """
    if expected is None:
        with pytest.raises(KeyError):
            manual.path_from_name(input)
    else:
        assert expected == manual.path_from_name(input)


def test_render_porcelain() -> None:
    """Test the Manual.render_porcelain method."""
    tree = manual.render_porcelain()
    # a list of expected lines **in the order in which they should occur**
    expected = [
        "1 - Commands",
        "+-- cobib.1",
        "+-- A - Common",
        # NOTE: we omit the first char in the next entry since it depends on the presence of plugins
        "-- B - Utility",
        "5 - Config",
        "`-- cobib-config.5",
        "7 - Miscellaneous",
        "+-- cobib-getting-started.7",
        "+-- A - Overview",
        "+-- B - Info",
        "+-- I - Importers",
        "`-- P - Parsers",
    ]
    # the index up to which we expect `tree` and `expected` to match exactly
    exact_index = 2
    # the index of expected which we have already found
    found_index = -1

    # loop over tree
    for idx, line in enumerate(tree):
        if idx <= exact_index:
            # perform exact matching
            assert line == expected[idx]
            found_index += 1
        elif expected[found_index + 1] in line:
            # NOTE: we perform a non-exact match to account for a possible additional `P - Plugin`
            # section which would render the first character of `B - Utility` differently

            # increment found index if line matches next expected one
            found_index += 1

        if found_index == len(expected) - 1:
            # if all expected sequences have been found, exit
            break

    # ensure all expected sequences were found
    assert found_index == len(expected) - 1
