"""Tests for coBib's Database class."""

from __future__ import annotations

import copy
import logging
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile
from typing import Any, cast

import pytest

from cobib.config import LabelSuffix, config
from cobib.database import Database, Entry
from cobib.database.database import CacheError

from .. import get_resource

TMPDIR = Path(tempfile.gettempdir())
EXAMPLE_LITERATURE = get_resource("example_literature.yaml")

DUMMY_ENTRY = Entry(
    "dummy",
    {
        "ENTRYTYPE": "misc",
        "author": "D. Dummy",
        "title": "Something dumb",
    },
)

DUMMY_ENTRY_YAML = """---
dummy:
    ENTRYTYPE: misc
    author:
      - first: D.
        last: Dummy
    title: Something dumb
...
"""


@pytest.fixture(autouse=True)
def setup() -> Generator[Any, None, None]:
    """Setup debugging configuration.

    This method also clears the `Database` after each test run.
    It is automatically enabled for all tests in this file.

    Yields:
        Access to the local fixture variables.
    """
    config.load(get_resource("debug.py"))
    Database().read()
    yield
    Database.reset()
    config.defaults()


def test_database_singleton() -> None:
    """Test the Database is a Singleton."""
    bib = Database()
    bib2 = Database()
    assert bib is bib2


def test_database_reset() -> None:
    """Test the Database.reset method."""
    bib = Database()
    assert len(bib.keys()) > 0
    assert bib._read
    Database.reset()
    assert len(bib.keys()) == 0
    assert not bib._read


def test_database_missing_file(caplog: pytest.LogCaptureFixture) -> None:
    """Test exit upon missing database file.

    Args:
        caplog: the built-in pytest fixture.
    """
    config.database.file = TMPDIR / "cobib_test_missing_file.yaml"
    try:
        with pytest.raises(SystemExit):
            Database().read()
        for source, level, message in caplog.record_tuples:
            if ("cobib.database.database", logging.CRITICAL) == (
                source,
                level,
            ) and f"The database file {config.database.file} does not exist!" in message:
                break
        else:
            pytest.fail("coBib did not exit upon encountering a missing database file!")
    finally:
        config.database.file = EXAMPLE_LITERATURE


def test_database_update() -> None:
    """Test the `cobib.database.Database.update` method."""
    entries = {"dummy1": "test1", "dummy2": "test2", "dummy3": "test3"}
    bib = Database()
    bib.update(entries)  # type: ignore

    assert Database._unsaved_entries == {e: e for e in list(entries.keys())}
    for key, val in entries.items():
        assert bib[key] == val


def test_database_pop() -> None:
    """Test the `cobib.database.Database.pop` method."""
    entries = {"dummy1": "test1", "dummy2": "test2", "dummy3": "test3"}
    bib = Database()
    bib.update(entries)  # type: ignore

    Database._unsaved_entries = {}
    assert Database._unsaved_entries == {}
    entry = bib.pop("dummy1")
    assert entry == "test1"
    assert "dummy1" not in bib.keys()
    assert Database._unsaved_entries == {"dummy1": None}


def test_database_rename() -> None:
    """Test the `cobib.database.Database.rename` method."""
    bib = Database()

    Database._unsaved_entries = {}
    assert Database._unsaved_entries == {}
    bib.rename("einstein", "dummy")

    assert Database._unsaved_entries == {"einstein": "dummy"}


@pytest.mark.parametrize(
    ["label_suffix", "expected"],
    [
        [("_", LabelSuffix.ALPHA), "test_a"],
        [("_", LabelSuffix.CAPITAL), "test_A"],
        [("_", LabelSuffix.NUMERIC), "test_1"],
        [(".", LabelSuffix.ALPHA), "test.a"],
        [(".", LabelSuffix.CAPITAL), "test.A"],
        [(".", LabelSuffix.NUMERIC), "test.1"],
    ],
)
def test_database_disambiguate_label(label_suffix: tuple[str, LabelSuffix], expected: str) -> None:
    """Test the `cobib.database.Database.disambiguate_label` method."""
    config.database.format.label_default = "test"
    config.database.format.label_suffix = label_suffix

    entries = {"dummy": "test", "test": "no"}
    bib = Database()
    bib.update(entries)  # type: ignore

    new_label = Database().disambiguate_label("test", entries["dummy"])  # type: ignore
    assert new_label == expected


@pytest.mark.parametrize(
    ["label", "label_suffix", "expected"],
    [
        [
            "Author2020",
            ("_", LabelSuffix.ALPHA),
            ({"Author2020", "Author2020_a"}, {"Author2020_1"}),
        ],
        [
            "Author2020",
            ("_", LabelSuffix.NUMERIC),
            ({"Author2020", "Author2020_1"}, {"Author2020_a"}),
        ],
        [
            "Author2020",
            ("_", LabelSuffix.CAPITAL),
            ({"Author2020"}, {"Author2020_1", "Author2020_a"}),
        ],
        [
            "Author2021",
            ("_", LabelSuffix.NUMERIC),
            ({"Author2021", "Author2021_2"}, set()),
        ],
    ],
)
def test_find_related_labels(
    label: str, label_suffix: tuple[str, LabelSuffix], expected: tuple[set[str], set[str]]
) -> None:
    """Test the `cobib.database.Database.find_related_labels` method.

    Args:
        label: the label to find related ones to.
        label_suffix: the value for the configuration setting.
        expected: the expected output of related labels based on the `disambiguation_database.yaml`.
    """
    config.database.file = get_resource("disambiguation_database.yaml", "database")
    config.database.format.label_suffix = label_suffix

    bib = Database()
    bib.read()

    direct, indirect = bib.find_related_labels(label)
    expected_direct, expected_indirect = expected
    assert expected_direct == direct
    assert expected_indirect == indirect


def test_database_read() -> None:
    """Test the `cobib.database.Database.read` method."""
    bib = Database()
    bib.read()

    assert Database._unsaved_entries == {}
    assert list(bib.keys()) == ["einstein", "latexcompanion", "knuthwebsite"]


def test_database_save_add() -> None:
    """Test the `cobib.database.Database.save` method after entry addition."""
    # prepare temporary database
    config.database.file = TMPDIR / "cobib_test_database_file.yaml"
    copyfile(EXAMPLE_LITERATURE, config.database.file)

    # initialize database
    bib = Database()
    bib.read()
    bib.update({"dummy": DUMMY_ENTRY})
    bib.save()

    expected = []
    with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as file:
        expected.extend(file.readlines())
    expected.extend(DUMMY_ENTRY_YAML.split("\n"))

    try:
        assert Database._unsaved_entries == {}

        with open(config.database.file, "r", encoding="utf-8") as file:
            # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
            for line, truth in zip(file, expected):
                assert line.strip() == truth.strip()
            with pytest.raises(StopIteration):
                next(file)
    finally:
        os.remove(config.database.file)
        config.database.file = EXAMPLE_LITERATURE


def test_database_save_modify() -> None:
    """Test the `cobib.database.Database.save` method after entry modification."""
    # prepare temporary database
    config.database.file = TMPDIR / "cobib_test_database_file.yaml"
    copyfile(EXAMPLE_LITERATURE, config.database.file)

    # initialize database
    bib = Database()
    bib.read()
    entry = copy.deepcopy(bib["einstein"])
    entry.data["tags"] = "test"
    bib.update({"einstein": entry})
    bib.save()

    try:
        assert Database._unsaved_entries == {}

        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    if "tags" in line:
                        assert line == "  tags: test\n"
                        # advance only the `file` iterator one step in order to catch up with the
                        # `expected` iterator
                        line = next(file)  # noqa: PLW2901
                    assert line == truth
                with pytest.raises(StopIteration):
                    next(file)
    finally:
        os.remove(config.database.file)
        config.database.file = EXAMPLE_LITERATURE


def test_database_save_delete() -> None:
    """Test the `cobib.database.Database.save` method after entry deletion."""
    # prepare temporary database
    config.database.file = TMPDIR / "cobib_test_database_file.yaml"
    copyfile(EXAMPLE_LITERATURE, config.database.file)

    # initialize database
    bib = Database()
    bib.read()
    bib.pop("knuthwebsite")
    bib.save()

    try:
        assert Database._unsaved_entries == {}

        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    assert line == truth
                with pytest.raises(StopIteration):
                    next(file)
    finally:
        os.remove(config.database.file)
        config.database.file = EXAMPLE_LITERATURE


def test_database_caching_disabled(caplog: pytest.LogCaptureFixture) -> None:
    """Tests that the caching mechanism can be disabled.

    Args:
        caplog: the built-in pytest fixture.
    """
    config.database.cache = None

    Database.reset()
    Database.read()

    assert (
        "cobib.database.database",
        10,
        "Encountered the following exception during cache lookup: "
        "'caching is disabled via the configuration'",
    ) in caplog.record_tuples


def test_database_cache_not_found() -> None:
    """Test the Database.read_cache method."""
    with tempfile.TemporaryDirectory() as tempdir:
        config.database.cache = tempdir

        Database.reset()

        with pytest.raises(CacheError, match="the database has not been cached yet"):
            Database.read_cache()


def test_database_save_cache() -> None:
    """Test the Database.save_cache method."""
    with tempfile.TemporaryDirectory() as tempdir:
        config.database.cache = tempdir

        Database.save_cache()

        with pytest.raises(OSError, match="Directory not empty"):
            Path(tempdir).rmdir()


def test_database_cache_uptodate(caplog: pytest.LogCaptureFixture) -> None:
    """Test Database.save_cache stops when the cache is up-to-date.

    Args:
        caplog: the built-in pytest fixture.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        config.database.cache = tempdir

        Database.save_cache()

        Database.save_cache()

    assert (
        "cobib.database.database",
        20,
        "The cache is already up-to-date",
    ) in caplog.record_tuples


def test_database_cache_reading(caplog: pytest.LogCaptureFixture) -> None:
    """Test that the Database.read method reads the cache.

    Args:
        caplog: the built-in pytest fixture.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        config.database.cache = tempdir

        Database.save_cache()
        Database.reset()
        Database.read()

    for record in caplog.record_tuples:
        if record[0] != "cobib.database.database":
            continue
        if record[1] != 10:
            continue
        if "Reading the cached database from " in record[2]:
            break
    else:
        pytest.fail("Log message not found which would indicate that Database.read_cache worked")


def test_database_cache_outdated() -> None:
    """Test Database.read_cache stops when the cache is outdated."""
    with tempfile.TemporaryDirectory() as tempdir:
        config.database.cache = tempdir
        config.database.file = Path(tempdir) / "cobib_test_database_file.yaml"
        copyfile(EXAMPLE_LITERATURE, config.database.file)

        Database.reset()
        Database.read()  # this will trigger save_cache, too

        cache_file = Database._get_cache_file()
        new_time = cast(Path, cache_file).stat().st_mtime_ns
        # make the cache appear outdated by updating the modified time of the database file
        os.utime(config.database.file, ns=(new_time + 1_000_000, new_time + 1_000_000))

        Database.reset()

        with pytest.raises(CacheError, match="the cached database is outdated"):
            Database.read_cache()
