"""Tests for coBib's Entry class."""

from __future__ import annotations

from typing import Any, Generator

import pytest

from cobib.config import AuthorFormat, config
from cobib.database import Author, Entry
from cobib.parsers.bibtex import BibtexParser
from cobib.utils.match import Match, Span
from cobib.utils.regex import HAS_OPTIONAL_REGEX
from cobib.utils.rel_path import RelPath

from .. import get_resource

EXAMPLE_BIBTEX_FILE = get_resource("example_entry.bib")
EXAMPLE_YAML_FILE = get_resource("example_entry.yaml")

EXAMPLE_ENTRY_DICT = {
    "ENTRYTYPE": "article",
    "author": "Max Rossmannek and Fabijan Pavošević and Angel Rubio and Ivano Tavernelli",
    "doi": "10.1021/acs.jpclett.3c00330",
    "issn": "1948-7185",
    "journal": "The Journal of Physical Chemistry Letters",
    "month": "apr",
    "number": 14,
    "pages": "3491–3497",  # noqa: RUF001
    "publisher": "American Chemical Society (ACS)",
    "title": (
        "Quantum Embedding Method for the Simulation of Strongly Correlated Systems on Quantum "
        "Computers"
    ),
    "url": ["http://dx.doi.org/10.1021/acs.jpclett.3c00330"],
    "volume": 14,
    "year": 2023,
}


@pytest.fixture(autouse=True)
def setup() -> Generator[Any, None, None]:
    """Setup debugging configuration.

    This method is automatically enabled for all tests in this file.

    Yields:
        Access to the local fixture variables.
    """
    config.load(get_resource("debug.py"))
    yield
    config.defaults()


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
    assert "ID" not in entry.data
    assert (
        "cobib.database.entry",
        20,
        "The field 'ID' of entry 'dummy' is no longer required. It will be inferred from the entry "
        "label.",
    ) in caplog.record_tuples


def test_equality() -> None:
    """Test entry equality."""
    entry_1 = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry_2 = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    # assert mutability of Entry
    assert entry_1 is not entry_2
    # assert equality of entries
    assert entry_1 == entry_2


def test_entry_set_label() -> None:
    """Test label changing."""
    # this test may fail if the input dict is not copied
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.label = "Rossmannek2023"
    assert entry.label == "Rossmannek2023"


def test_entry_set_tags(caplog: pytest.LogCaptureFixture) -> None:
    """Test tags setting.

    Args:
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    assert entry.tags == []
    # NB: tags must be a list
    entry.tags = ["foo"]
    assert entry.tags == ["foo"]
    # list works as expected
    entry.tags = ["foo", "bar"]
    assert entry.tags == ["foo", "bar"]
    # check lint logging
    entry.tags = "foo, bar"  # type: ignore[assignment]
    assert entry.tags == ["foo", "bar"]
    assert (
        "cobib.database.entry",
        20,
        "Converted the field 'tags' of entry 'Rossmannek_2023' to a list. You can consider storing "
        "it as such directly.",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    "files",
    [
        [EXAMPLE_BIBTEX_FILE],
        [EXAMPLE_BIBTEX_FILE, EXAMPLE_YAML_FILE],
    ],
)
def test_entry_set_file(files: list[str], caplog: pytest.LogCaptureFixture) -> None:
    """Test file setting.

    Args:
        files: a list of paths to files.
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.file = files[0] if len(files) == 1 else files  # type: ignore[assignment]
    expected = [str(RelPath(file)) for file in files]
    assert entry.file == expected
    # check lint logging
    if len(files) > 1:
        entry.file = ", ".join(files)  # type: ignore[assignment]
        assert entry.file == expected
        assert (
            "cobib.database.entry",
            20,
            "Converted the field 'file' of entry 'Rossmannek_2023' to a list. You can consider "
            "storing it as such directly.",
        ) in caplog.record_tuples


def test_entry_set_url(caplog: pytest.LogCaptureFixture) -> None:
    """Test url setting.

    Args:
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.url = "https://dummy.org/, https://dummy.com/"  # type: ignore[assignment]
    assert entry.url == ["https://dummy.org/", "https://dummy.com/"]
    assert (
        "cobib.database.entry",
        20,
        "Converted the field 'url' of entry 'Rossmannek_2023' to a list. You can consider storing "
        "it as such directly.",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    ["month", "expected"],
    [
        [(1, "1", "January"), "jan"],
        [(2, "2", "February"), "feb"],
        [(3, "3", "March"), "mar"],
        [(4, "4", "April"), "apr"],
        [(5, "5", "May"), "may"],
        [(6, "6", "June"), "jun"],
        [(7, "7", "July"), "jul"],
        [(8, "8", "August"), "aug"],
        [(9, "9", "September"), "sep"],
        [(10, "10", "October"), "oct"],
        [(11, "11", "November"), "nov"],
        [(12, "12", "December"), "dec"],
    ],
)
def test_entry_set_month(
    month: tuple[int, str, str], expected: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test month setting.

    Args:
        month: a triple containing the month index (as integer and string) and the full name.
        expected: the expected three-letter code of the month.
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    assert entry.data["month"] == "apr"
    for m in month:
        entry.month = m  # type: ignore[assignment]
        assert entry.data["month"] == expected
        assert (
            "cobib.database.entry",
            20,
            f"Converting field 'month' of entry 'Rossmannek_2023' from '{m}' to '{expected}'.",
        ) in caplog.record_tuples


@pytest.mark.parametrize(
    ["filter_", "or_", "ignore_case"],
    [
        [{("author", True): ["rossmannek"]}, False, True],
        [{("author", True): ["Rossmannek"]}, False, False],
        [{("author", False): ["wrong_author"]}, False, False],
        [{("author", True): ["rossmannek"], ("year", True): ["2023"]}, False, True],
        [{("author", True): ["Rossmannek"], ("year", True): ["2023"]}, False, False],
        [{("author", True): ["Rossmannek"], ("year", True): ["2020"]}, True, False],
        [{("author", True): ["wrong_author"], ("year", True): ["2023"]}, True, False],
        [{("author", False): ["wrong_author"], ("year", True): ["2023"]}, False, False],
        [{("label", True): [r"\D+_\d+"]}, True, False],
    ],
)
def test_entry_matches(
    filter_: dict[tuple[str, bool], list[str]], or_: bool, ignore_case: bool
) -> None:
    """Test match filter.

    Args:
        filter_: a filter as explained be `cobib.database.Entry.matches`.
        or_: whether to use logical `OR` rather than `AND` for filter combination.
        ignore_case: whether to perform the filter matching case *in*sensitive.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    # author must match
    assert entry.matches(filter_, or_=or_, ignore_case=ignore_case)


@pytest.mark.parametrize(
    ["filter", "title", "decode_latex", "decode_unicode"],
    [
        [
            "Kör",
            r"Zur Elektrodynamik bewegter K{\"o}rper",
            True,
            False,
        ],
        [
            "Kor",
            "Zur Elektrodynamik bewegter Körper",
            False,
            True,
        ],
        [
            "Kor",
            r"Zur Elektrodynamik bewegter K{\"o}rper",
            True,
            True,
        ],
    ],
)
def test_matches_decoding(
    filter: str, title: str, decode_latex: bool, decode_unicode: bool
) -> None:
    """Test the `cobib.database.Entry.matches` method's decoding arguments."""
    entry = Entry(
        "search_dummy",
        {
            "ENTRYTYPE": "article",
            "title": title,
        },
    )
    assert entry.matches(
        {
            ("title", True): [filter],
        },
        or_=False,
        decode_latex=decode_latex,
        decode_unicode=decode_unicode,
    )


@pytest.mark.parametrize(
    ["filter_", "expected", "fuzziness"],
    [
        [
            {("journal", True): ["Letters"]},
            True,
            0,
        ],
        [
            {("journal", True): ["Lettesr"]},
            False,
            0,
        ],
        [
            {("journal", True): ["Lettesr"]},
            True,
            1,
        ],
    ],
)
def test_matches_fuzziness(
    filter_: dict[tuple[str, bool], list[str]], expected: bool, fuzziness: int
) -> None:
    """Test the `cobib.database.Entry.matches` method's fuzziness arguments."""
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    result = entry.matches(filter_, or_=False, fuzziness=fuzziness)
    if fuzziness > 0 and not HAS_OPTIONAL_REGEX:
        assert result is False
    else:
        assert result is expected


def test_match_with_wrong_key() -> None:
    """Asserts issue #1 is fixed.

    When `cobib.database.Entry.matches` is called with a key in the filter which does not exist in
    the entry, the key should be ignored and the function should return normally.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    filter_ = {("tags", False): ["test"]}
    assert entry.matches(filter_, or_=False)


@pytest.mark.parametrize(
    ["query", "context", "ignore_case", "expected"],
    [
        [
            ["search_query"],
            1,
            False,
            [
                Match(
                    "@article{search_dummy,\n abstract = {search_query\nsomething else",
                    [Span(36, 48)],
                ),
                Match("something else\nsearch_query\nsomething else", [Span(15, 27)]),
            ],
        ],
        [
            ["search_query"],
            1,
            True,
            [
                Match(
                    "@article{search_dummy,\n abstract = {search_query\nsomething else",
                    [Span(36, 48)],
                ),
                Match("something else\nSearch_Query\nsomething else", [Span(15, 27)]),
                Match("something else\nsearch_query\nsomething else", [Span(15, 27)]),
                Match("something else\nSearch_Query\nsomething else}", [Span(15, 27)]),
            ],
        ],
        [
            ["[sS]earch_[qQ]uery"],
            1,
            False,
            [
                Match(
                    "@article{search_dummy,\n abstract = {search_query\nsomething else",
                    [Span(36, 48)],
                ),
                Match("something else\nSearch_Query\nsomething else", [Span(15, 27)]),
                Match("something else\nsearch_query\nsomething else", [Span(15, 27)]),
                Match("something else\nSearch_Query\nsomething else}", [Span(15, 27)]),
            ],
        ],
        [
            ["search_query"],
            2,
            False,
            [
                Match(
                    (
                        "@article{search_dummy,\n"
                        " abstract = {search_query\n"
                        "something else\n"
                        "Search_Query"
                    ),
                    [Span(36, 48)],
                ),
                Match(
                    ("Search_Query\nsomething else\nsearch_query\nsomething else\nSearch_Query"),
                    [Span(28, 40)],
                ),
            ],
        ],
        # the following will look almost identical to the second scenarios because otherwise the
        # next match would be included within the context.
        [
            ["search_query"],
            2,
            True,
            [
                Match(
                    "@article{search_dummy,\n abstract = {search_query\nsomething else",
                    [Span(36, 48)],
                ),
                Match("something else\nSearch_Query\nsomething else", [Span(15, 27)]),
                Match("something else\nsearch_query\nsomething else", [Span(15, 27)]),
                Match("something else\nSearch_Query\nsomething else}\n}", [Span(15, 27)]),
            ],
        ],
        # what we care about here, is that the second match does not include lines which occur
        # *before* the first match.
        [
            ["search_query"],
            10,
            False,
            [
                Match(
                    (
                        "@article{search_dummy,\n"
                        " abstract = {search_query\n"
                        "something else\n"
                        "Search_Query\n"
                        "something else"
                    ),
                    [Span(36, 48)],
                ),
                Match(
                    (
                        "something else\n"
                        "Search_Query\n"
                        "something else\n"
                        "search_query\n"
                        "something else\n"
                        "Search_Query\n"
                        "something else}\n"
                        "}\n"
                        ""
                    ),
                    [Span(43, 55)],
                ),
            ],
        ],
        [
            ["query", "Query"],
            1,
            False,
            [
                Match(
                    "@article{search_dummy,\n abstract = {search_query\nsomething else",
                    [Span(43, 48)],
                ),
                Match("something else\nsearch_query\nsomething else", [Span(22, 27)]),
                Match("something else\nSearch_Query\nsomething else", [Span(22, 27)]),
                Match("something else\nSearch_Query\nsomething else}", [Span(22, 27)]),
            ],
        ],
    ],
)
def test_search(query: list[str], context: int, ignore_case: bool, expected: list[Match]) -> None:
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


@pytest.mark.parametrize(
    ["query", "title", "decode_latex", "decode_unicode"],
    [
        [
            "Kör",
            r"Zur Elektrodynamik bewegter K{\"o}rper",
            True,
            False,
        ],
        [
            "Kor",
            "Zur Elektrodynamik bewegter Körper",
            False,
            True,
        ],
        [
            "Kor",
            r"Zur Elektrodynamik bewegter K{\"o}rper",
            True,
            True,
        ],
    ],
)
def test_search_decoding(query: str, title: str, decode_latex: bool, decode_unicode: bool) -> None:
    """Test the `cobib.database.Entry.search` method's decoding arguments."""
    entry = Entry(
        "search_dummy",
        {
            "ENTRYTYPE": "article",
            "title": title,
        },
    )
    results = entry.search(
        [query], context=0, decode_latex=decode_latex, decode_unicode=decode_unicode
    )
    assert results == [Match(f" title = {{{title}}}", [Span(38, 41)])]


@pytest.mark.parametrize(
    ["query", "expected", "fuzziness"],
    [
        [
            "Letters",
            [
                Match(
                    " journal = {The Journal of Physical Chemistry Letters},",
                    [Span(start=46, end=53)],
                )
            ],
            0,
        ],
        [
            "Lettesr",
            [],
            0,
        ],
        [
            "Lettesr",
            [
                Match(
                    " journal = {The Journal of Physical Chemistry Letters},",
                    [Span(start=46, end=52)],
                )
            ],
            1,
        ],
    ],
)
def test_search_fuzziness(query: str, expected: list[Match], fuzziness: int) -> None:
    """Test the `cobib.database.Entry.search` method's fuzziness arguments."""
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    results = entry.search([query], context=0, fuzziness=fuzziness)
    if fuzziness > 0 and not HAS_OPTIONAL_REGEX:
        assert results == []
    else:
        assert results == expected


def test_search_with_file() -> None:
    """Test the `cobib.database.Entry.search` method with associated file."""
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.file = EXAMPLE_YAML_FILE  # type: ignore[assignment]
    results = entry.search(["Chem"], context=0)
    expected = [
        Match(" journal = {The Journal of Physical Chemistry Letters},", [Span(36, 40)]),
        Match(" publisher = {American Chemical Society (ACS)},", [Span(23, 27)]),
        Match("journal: The Journal of Physical Chemistry Letters", [Span(33, 37)]),
        Match("publisher: American Chemical Society (ACS)", [Span(20, 24)]),
    ]
    assert len(results) == len(expected)
    for res, exp in zip(results, expected):
        assert res == exp


def test_search_with_skipped_file() -> None:
    """Test the `cobib.database.Entry.search` method with skipping the associated file."""
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.file = EXAMPLE_YAML_FILE  # type: ignore[assignment]
    results = entry.search(["Chem"], context=0, skip_files=True)
    expected = [
        Match(" journal = {The Journal of Physical Chemistry Letters},", [Span(36, 40)]),
        Match(" publisher = {American Chemical Society (ACS)},", [Span(23, 27)]),
    ]
    assert len(results) == len(expected)
    for res, exp in zip(results, expected):
        assert res == exp


def test_search_with_missing_file(caplog: pytest.LogCaptureFixture) -> None:
    """Test the `cobib.database.Entry.search` method with a missing file.

    Args:
        caplog: the built-in pytest fixture.
    """
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.file = "some_non_existent_file.txt"  # type: ignore[assignment]
    _ = entry.search(["Chemical"], context=0)
    for source, level, message in caplog.record_tuples:
        if level != 30 or source != "cobib.database.entry":
            continue
        if message.startswith("The associated file") and message.endswith(
            "of entry Rossmannek_2023 does not exist!"
        ):
            break
    else:
        pytest.fail("Missing file was not logged.")


@pytest.mark.parametrize("author_format", [AuthorFormat.BIBLATEX, AuthorFormat.YAML])
def test_formatted(author_format: AuthorFormat) -> None:
    """Test the special formatting of entries.

    This also ensures that special characters in the label remain unchanged.
    """
    config.database.format.author_format = author_format
    reference: dict[str, Any] = {
        "ENTRYTYPE": "book",
        "title": 'LaTeX Einf{\\"u}hrung',
    }
    if author_format == AuthorFormat.BIBLATEX:
        reference["author"] = 'Mustermann, Max and M{\\"u}ller, Mara'
    elif author_format == AuthorFormat.YAML:
        reference["author"] = [
            Author("Max", "Mustermann"),
            Author("Mara", "Müller"),
        ]
    entries = BibtexParser().parse(get_resource("example_entry_umlaut.bib", "database"))
    entry = next(iter(entries.values()))
    formatted = entry.formatted()
    assert formatted.data == reference
    assert formatted.label == "LaTeX_Einführung"


def test_verbatim_fields() -> None:
    """Tests the `config.database.format.verbatim_fields` setting."""
    entry = Entry("LaTeX_Einfuhrung", {"title": "LaTeX Einführung"})

    formatted = entry.formatted()
    config.database.format.verbatim_fields += ["title"]
    assert formatted.data["title"] == 'LaTeX Einf{\\"u}hrung'

    try:
        formatted = entry.formatted()
        config.database.format.verbatim_fields += ["title"]
        assert formatted.data["title"] == "LaTeX Einführung"
    finally:
        config.defaults()


@pytest.mark.parametrize(
    ["author_format", "reference_file"],
    [
        (
            AuthorFormat.BIBLATEX,
            get_resource("example_entry_author_format_biblatex.yaml", "database"),
        ),
        (AuthorFormat.YAML, get_resource("example_entry.yaml")),
    ],
)
def test_save(author_format: AuthorFormat, reference_file: str) -> None:
    """Test the `cobib.database.Entry.save` method."""
    config.database.format.author_format = author_format
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry_str = entry.save()
    with open(reference_file, "r", encoding="utf-8") as expected:
        for line, truth in zip(entry_str.split("\n"), expected):
            if "pages" in line:
                # NOTE: we skip this check because of the \textendash character being annoying
                continue
            assert line == truth.strip("\n")


def test_merge_ours() -> None:
    """Test the `cobib.database.Entry.merge` method with the `ours` strategy."""
    entry = Entry(
        "dummy",
        {"month": "jan", "year": 2024},
    )
    theirs = Entry(
        "dummy",
        {"month": "feb", "number": 1},
    )
    entry.merge(theirs, ours=True)
    assert entry.data["number"] == 1
    assert entry.data["month"] == "jan"
    assert entry.data["year"] == 2024


def test_merge_theirs() -> None:
    """Test the `cobib.database.Entry.merge` method with the `theirs` strategy."""
    entry = Entry(
        "dummy",
        {"month": "jan", "year": 2024},
    )
    theirs = Entry(
        "dummy",
        {"month": "feb", "number": 1},
    )
    entry.merge(theirs, ours=False)
    assert entry.data["number"] == 1
    assert entry.data["month"] == "feb"
    assert entry.data["year"] == 2024


def test_stringify() -> None:
    """Test the `cobib.database.Entry.stringify` method."""
    entry = Entry(
        "dummy",
        {
            "file": ["/tmp/a.txt", "/tmp/b.txt"],
            "month": 4,
            "tags": ["tag1", "tag2"],
        },
    )
    expected = {
        "label": "dummy",
        "file": "/tmp/a.txt, /tmp/b.txt",
        "month": "apr",
        "tags": "tag1, tag2",
    }
    assert entry.stringify() == expected


def test_markup_label() -> None:
    """Test the `cobib.database.Entry.markup_label` method."""
    entry = Entry("Rossmannek_2023", EXAMPLE_ENTRY_DICT)
    entry.tags = ["new", "medium"]
    markup_label = entry.markup_label()
    assert markup_label == "[tag.new][tag.medium]Rossmannek_2023[/tag.medium][/tag.new]"
