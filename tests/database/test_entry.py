"""Tests for coBib's Entry class."""

from typing import Any, Dict, List, Tuple

import pytest

from cobib.database import Entry
from cobib.parsers.bibtex import BibtexParser
from cobib.utils.rel_path import RelPath

from .. import get_resource

EXAMPLE_BIBTEX_FILE = get_resource("example_entry.bib")
EXAMPLE_YAML_FILE = get_resource("example_entry.yaml")

EXAMPLE_ENTRY_DICT = {
    "ENTRYTYPE": "article",
    "author": "Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and Peter"
    + " D. Johnson and M{\\'a}ria Kieferov{\\'a} and Ian D. Kivlichan and Tim Menke and Borja "
    + "Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and Al{\\'a}n Aspuru-Guzik",
    "doi": "10.1021/acs.chemrev.8b00803",
    "journal": "Chemical Reviews",
    "month": "aug",
    "number": 19,
    "pages": "10856--10915",
    "publisher": "American Chemical Society ({ACS})",
    "title": "Quantum Chemistry in the Age of Quantum Computing",
    "url": "https://doi.org/10.1021%2Facs.chemrev.8b00803",
    "volume": 119,
    "year": 2019,
}


def test_init_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Test init logging for linting purposes.

    Args:
        caplog: the built-in pytest fixture.
    """
    entry = Entry("dummy", {"ID": "dummy", "number": "1"})
    assert entry.data["number"] == 1
    assert (
        "cobib.database.entry",
        20,
        "Converting field 'number' of entry 'dummy' to integer: 1.",
    ) in caplog.record_tuples
    assert entry.label == "dummy"
    assert "ID" not in entry.data.keys()
    assert (
        "cobib.database.entry",
        20,
        "The field 'ID' of entry 'dummy' is no longer required. It will be inferred from the entry "
        "label.",
    ) in caplog.record_tuples


def test_equality() -> None:
    """Test entry equality."""
    entry_1 = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry_2 = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    # assert mutability of Entry
    assert entry_1 is not entry_2
    # assert equality of entries
    assert entry_1 == entry_2


def test_entry_set_label() -> None:
    """Test label changing."""
    # this test may fail if the input dict is not copied
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.label = "Cao2019"
    assert entry.label == "Cao2019"


def test_entry_set_tags(caplog: pytest.LogCaptureFixture) -> None:
    """Test tags setting.

    Args:
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    assert entry.tags == []
    # NB: tags must be a list
    entry.tags = ["foo"]
    assert entry.tags == ["foo"]
    # list works as expected
    entry.tags = ["foo", "bar"]
    assert entry.tags == ["foo", "bar"]
    # check lint logging
    entry.tags = "foo, bar"  # type: ignore
    assert entry.tags == ["foo", "bar"]
    assert (
        "cobib.database.entry",
        20,
        "Converted the field 'tags' of entry 'Cao_2019' to a list. You can consider storing it as "
        "such directly.",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    "files",
    [
        [EXAMPLE_BIBTEX_FILE],
        [EXAMPLE_BIBTEX_FILE, EXAMPLE_YAML_FILE],
    ],
)
def test_entry_set_file(files: List[str], caplog: pytest.LogCaptureFixture) -> None:
    """Test file setting.

    Args:
        files: a list of paths to files.
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.file = files[0] if len(files) == 1 else files  # type: ignore
    expected = [str(RelPath(file)) for file in files]
    assert entry.file == expected
    # check lint logging
    if len(files) > 1:
        entry.file = ", ".join(files)  # type: ignore
        assert entry.file == expected
        assert (
            "cobib.database.entry",
            20,
            "Converted the field 'file' of entry 'Cao_2019' to a list. You can consider storing it "
            "as such directly.",
        ) in caplog.record_tuples


def test_entry_set_url(caplog: pytest.LogCaptureFixture) -> None:
    """Test url setting.

    Args:
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.url = "https://dummy.org/, https://dummy.com/"  # type: ignore
    assert entry.url == ["https://dummy.org/", "https://dummy.com/"]
    assert (
        "cobib.database.entry",
        20,
        "Converted the field 'url' of entry 'Cao_2019' to a list. You can consider storing it as "
        "such directly.",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    ["month", "expected"],
    [
        [(1, "January"), "jan"],
        [(2, "February"), "feb"],
        [(3, "March"), "mar"],
        [(4, "April"), "apr"],
        [(5, "May"), "may"],
        [(6, "June"), "jun"],
        [(7, "July"), "jul"],
        [(8, "August"), "aug"],
        [(9, "September"), "sep"],
        [(10, "October"), "oct"],
        [(11, "November"), "nov"],
        [(12, "December"), "dec"],
    ],
)
def test_entry_set_month(
    month: Tuple[int, str], expected: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test month setting.

    Args:
        month: a pair containing the month index and full name.
        expected: the expected three-letter code of the month.
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    assert entry.data["month"] == "aug"
    entry.month = month[0]  # type: ignore
    assert entry.data["month"] == expected
    assert (
        "cobib.database.entry",
        20,
        f"Converting field 'month' of entry 'Cao_2019' from '{month[0]}' to '{expected}'.",
    ) in caplog.record_tuples
    entry.month = month[1]
    assert entry.data["month"] == expected
    assert (
        "cobib.database.entry",
        20,
        f"Converting field 'month' of entry 'Cao_2019' from '{month[1]}' to '{expected}'.",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    ["filter_", "or_"],
    [
        [{("author", True): ["Cao"]}, False],
        [{("author", False): ["wrong_author"]}, False],
        [{("author", True): ["Cao"], ("year", True): ["2019"]}, False],
        [{("author", True): ["Cao"], ("year", True): ["2020"]}, True],
        [{("author", True): ["wrong_author"], ("year", True): ["2019"]}, True],
        [{("author", False): ["wrong_author"], ("year", True): ["2019"]}, False],
        [{("label", True): [r"\D+_\d+"]}, True],
    ],
)
def test_entry_matches(filter_: Dict[Tuple[str, bool], Any], or_: bool) -> None:
    """Test match filter.

    Args:
        filter_: a filter as explained be `cobib.database.Entry.matches`.
        or_: whether to use logical `OR` rather than `AND` for filter combination.
    """
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    # author must match
    assert entry.matches(filter_, or_=or_)


def test_match_with_wrong_key() -> None:
    """Asserts issue #1 is fixed.

    When `cobib.database.Entry.matches` is called with a key in the filter which does not exist in
    the entry, the key should be ignored and the function should return normally.
    """
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    filter_ = {("tags", False): ["test"]}
    assert entry.matches(filter_, or_=False)


@pytest.mark.parametrize(
    ["query", "context", "ignore_case", "expected"],
    [
        [
            "search_query",
            1,
            False,
            [
                ["@article{search_dummy,", " abstract = {search_query", "something else"],
                ["something else", "search_query", "something else"],
            ],
        ],
        [
            "search_query",
            1,
            True,
            [
                ["@article{search_dummy,", " abstract = {search_query", "something else"],
                ["something else", "Search_Query", "something else"],
                ["something else", "search_query", "something else"],
                ["something else", "Search_Query", "something else}"],
            ],
        ],
        [
            "[sS]earch_[qQ]uery",
            1,
            False,
            [
                ["@article{search_dummy,", " abstract = {search_query", "something else"],
                ["something else", "Search_Query", "something else"],
                ["something else", "search_query", "something else"],
                ["something else", "Search_Query", "something else}"],
            ],
        ],
        [
            "search_query",
            2,
            False,
            [
                [
                    "@article{search_dummy,",
                    " abstract = {search_query",
                    "something else",
                    "Search_Query",
                ],
                [
                    "Search_Query",
                    "something else",
                    "search_query",
                    "something else",
                    "Search_Query",
                ],
            ],
        ],
        # the following will look almost identical to the second scenarios because otherwise the
        # next match would be included within the context.
        [
            "search_query",
            2,
            True,
            [
                ["@article{search_dummy,", " abstract = {search_query", "something else"],
                ["something else", "Search_Query", "something else"],
                ["something else", "search_query", "something else"],
                ["something else", "Search_Query", "something else}", "}"],
            ],
        ],
        # what we care about here, is that the second match does not include lines which occur
        # *before* the first match.
        [
            "search_query",
            10,
            False,
            [
                [
                    "@article{search_dummy,",
                    " abstract = {search_query",
                    "something else",
                    "Search_Query",
                    "something else",
                ],
                [
                    "something else",
                    "Search_Query",
                    "something else",
                    "search_query",
                    "something else",
                    "Search_Query",
                    "something else}",
                    "}",
                    "",
                    "",
                ],
            ],
        ],
    ],
)
def test_search(query: str, context: int, ignore_case: bool, expected: List[List[str]]) -> None:
    """Test search method.

    Args:
        query: the string to search for.
        context: the number of lines to provide as context for the search results.
        ignore_case: whether to perform a case-insensitive search.
        expected: the expected lines.
    """
    entry = Entry(
        "search_dummy",
        {
            "ENTRYTYPE": "article",
            "abstract": "\n".join(
                [
                    "search_query",
                    "something else",
                    "Search_Query",
                    "something else",
                ]
                * 2
            ),
        },
    )
    results = entry.search(query, context=context, ignore_case=ignore_case)
    assert results == expected


def test_search_with_file() -> None:
    """Test the `cobib.database.Entry.search` method with associated file."""
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.file = EXAMPLE_YAML_FILE  # type: ignore
    results = entry.search("Chemical", context=0)
    expected = [
        [" journal = {Chemical Reviews},"],
        [" publisher = {American Chemical Society ({ACS})},"],
        ["journal: Chemical Reviews"],
        ["publisher: American Chemical Society ({ACS})"],
    ]
    for res, exp in zip(results, expected):
        assert res == exp


def test_escape_special_chars() -> None:
    """Test escaping of special characters.

    This also ensures that special characters in the label remain unchanged.
    """
    reference = {
        "ENTRYTYPE": "book",
        "title": 'LaTeX Einf{\\"u}hrung',
    }
    entries = BibtexParser().parse(get_resource("example_entry_umlaut.bib", "database"))
    entry = list(entries.values())[0]
    entry.escape_special_chars()
    assert entry.data == reference
    assert entry.label == "LaTeX_Einführung"


def test_save() -> None:
    """Test the `cobib.database.Entry.save` method."""
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry_str = entry.save()
    with open(EXAMPLE_YAML_FILE, "r", encoding="utf-8") as expected:
        for line, truth in zip(entry_str.split("\n"), expected):
            assert line == truth.strip("\n")


def test_stringify() -> None:
    """Test the `cobib.database.Entry.stringify` method."""
    entry = Entry(
        "dummy",
        {
            "file": ["/tmp/a.txt", "/tmp/b.txt"],
            "month": 8,
            "tags": ["tag1", "tag2"],
        },
    )
    expected = {
        "label": "dummy",
        "file": "/tmp/a.txt, /tmp/b.txt",
        "month": "aug",
        "tags": "tag1, tag2",
    }
    assert entry.stringify() == expected
