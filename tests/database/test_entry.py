"""Tests for coBib's Entry class."""

import pytest

from cobib.config import config
from cobib.database import Entry
from cobib.parsers import BibtexParser

from .. import get_path_relative_to_home, get_resource

EXAMPLE_BIBTEX_FILE = get_resource("example_entry.bib")
EXAMPLE_YAML_FILE = get_resource("example_entry.yaml")

EXAMPLE_ENTRY_DICT = {
    "ENTRYTYPE": "article",
    "ID": "Cao_2019",
    "author": "Yudong Cao and Jonathan Romero and Jonathan P. Olson and Matthias Degroote and Peter"
    + " D. Johnson and M{\\'a}ria Kieferov{\\'a} and Ian D. Kivlichan and Tim Menke and Borja "
    + "Peropadre and Nicolas P. D. Sawaya and Sukin Sim and Libor Veis and Al{\\'a}n Aspuru-Guzik",
    "doi": "10.1021/acs.chemrev.8b00803",
    "journal": "Chemical Reviews",
    "month": "8",
    "number": "19",
    "pages": "10856--10915",
    "publisher": "American Chemical Society ({ACS})",
    "title": "Quantum Chemistry in the Age of Quantum Computing",
    "url": "https://doi.org/10.1021%2Facs.chemrev.8b00803",
    "volume": "119",
    "year": "2019",
}


def test_equality():
    """Test entry equality."""
    entry_1 = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry_2 = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    # assert mutability of Entry
    assert entry_1 is not entry_2
    # assert equality of entries
    assert entry_1 == entry_2


def test_mismatching_label_id_fix():
    """Test that the label takes precedence over the label upon mismatch."""
    entry = Entry("Cao2019", EXAMPLE_ENTRY_DICT)
    assert entry.label == "Cao2019"
    assert entry.data["ID"] == "Cao2019"


def test_entry_set_label():
    """Test label changing."""
    # this test may fail if the input dict is not copied
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.label = "Cao2019"
    assert entry.label == "Cao2019"
    assert entry.data["ID"] == "Cao2019"


def test_entry_set_tags():
    """Test tags setting."""
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    assert entry.tags is None
    # NB: tags must be a list
    entry.tags = ["foo"]
    assert entry.tags == "foo"
    # '+' signs are stripped
    entry.tags = ["+foo"]
    assert entry.tags == "foo"
    # also multiple occurrences
    entry.tags = ["++foo"]
    assert entry.tags == "foo"
    # list works as expected
    entry.tags = ["foo", "bar"]
    assert entry.tags == "foo, bar"
    entry.tags = ["+foo", "bar"]
    assert entry.tags == "foo, bar"
    entry.tags = ["+foo", "+bar"]
    assert entry.tags == "foo, bar"


@pytest.mark.parametrize(
    "files",
    [
        [EXAMPLE_BIBTEX_FILE],
        [EXAMPLE_BIBTEX_FILE, EXAMPLE_YAML_FILE],
    ],
)
def test_entry_set_file(files):
    """Test file setting."""
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.file = files[0] if len(files) == 1 else files
    expected = ", ".join([get_path_relative_to_home(file) for file in files])
    assert entry.data["file"] == expected


@pytest.mark.parametrize(
    ["filter_", "or_"],
    [
        [{("author", True): ["Cao"]}, False],
        [{("author", False): ["wrong_author"]}, False],
        [{("author", True): ["Cao"], ("year", True): ["2019"]}, False],
        [{("author", True): ["Cao"], ("year", True): ["2020"]}, True],
        [{("author", True): ["wrong_author"], ("year", True): ["2019"]}, True],
        [{("author", False): ["wrong_author"], ("year", True): ["2019"]}, False],
    ],
)
def test_entry_matches(filter_, or_):
    """Test match filter."""
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    # author must match
    assert entry.matches(filter_, or_=or_)


def test_match_with_wrong_key():
    """Asserts issue #1 is fixed.

    When matches() is called with a key in the filter which does not exist in the entry, the key
    should be ignored and the function should return normally.
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
def test_search(query, context, ignore_case, expected):
    """Test search method."""
    entry = Entry(
        "search_dummy",
        {
            "ENTRYTYPE": "article",
            "ID": "search_dummy",
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


def test_search_with_file():
    """Test search method with associated file."""
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry.file = EXAMPLE_YAML_FILE
    results = entry.search("Chemical", context=0)
    print(results)
    expected = [
        [" journal = {Chemical Reviews},"],
        [" publisher = {American Chemical Society ({ACS})},"],
        ["journal: Chemical Reviews"],
        ["publisher: American Chemical Society ({ACS})"],
    ]
    for res, exp in zip(results, expected):
        assert res == exp


@pytest.mark.parametrize("original_type", [int, str])
@pytest.mark.parametrize("converted_type", [int, str])
def test_month_conversion(original_type, converted_type):
    """Test month conversion.

    Args:
        original_type (type): original type which to convert from.
        converted_type (type): type to use for storing the 'month' field.
    """
    config.load(get_resource("debug.py"))
    config.database.format.month = converted_type
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    if original_type == int:
        entry.data["month"] = "8"
    elif original_type == str:
        entry.data["month"] = "aug"

    entry.convert_month(converted_type)

    if converted_type == int:
        assert entry.data["month"] == "8"
    elif converted_type == str:
        assert entry.data["month"] == "aug"


def test_escape_special_chars():
    """Test escaping of special characters.

    This also tests ensures that special characters in the label remain unchanged.
    """
    reference = {
        "ENTRYTYPE": "book",
        "ID": "LaTeX_Einführung",
        "title": 'LaTeX Einf{\\"u}hrung',
    }
    entries = BibtexParser().parse(get_resource("example_entry_umlaut.bib", "database"))
    entry = list(entries.values())[0]
    entry.escape_special_chars()
    assert entry.data == reference


def test_save():
    """Test save method."""
    config.database.format.month = int
    entry = Entry("Cao_2019", EXAMPLE_ENTRY_DICT)
    entry_str = entry.save()
    with open(EXAMPLE_YAML_FILE, "r") as expected:
        for line, truth in zip(entry_str.split("\n"), expected):
            assert line == truth.strip("\n")
