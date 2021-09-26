"""Tests for coBib's Database class."""

import copy
import logging
import os
import tempfile
from pathlib import Path
from shutil import copyfile
from typing import Any, Callable, Generator, Tuple

import pytest

from cobib.config import LabelSuffix, config
from cobib.database import Database, Entry

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
    author: D. Dummy
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
    yield
    Database().clear()
    config.defaults()


def test_database_singleton() -> None:
    """Test the Database is a Singleton."""
    bib = Database()
    bib2 = Database()
    assert bib is bib2


def test_database_missing_file(caplog: pytest.LogCaptureFixture) -> None:
    """Test exit upon missing database file.

    Args:
        caplog: the built-in pytest fixture.
    """
    config.database.file = TMPDIR / "cobib_test_missing_file.yaml"
    try:
        with pytest.raises(SystemExit):
            Database().read()
        for (source, level, message) in caplog.record_tuples:
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
    # pylint: disable=protected-access
    assert Database._unsaved_entries == {e: e for e in list(entries.keys())}
    for key, val in entries.items():
        assert bib[key] == val


def test_database_pop() -> None:
    """Test the `cobib.database.Database.pop` method."""
    entries = {"dummy1": "test1", "dummy2": "test2", "dummy3": "test3"}
    bib = Database()
    bib.update(entries)  # type: ignore
    # pylint: disable=protected-access
    Database._unsaved_entries = {}
    assert Database._unsaved_entries == {}
    entry = bib.pop("dummy1")
    assert entry == "test1"
    assert "dummy1" not in bib.keys()
    assert Database._unsaved_entries == {"dummy1": None}


def test_database_rename() -> None:
    """Test the `cobib.database.Database.rename` method."""
    bib = Database()
    # pylint: disable=protected-access
    Database._unsaved_entries = {}
    assert Database._unsaved_entries == {}
    bib.rename("einstein", "dummy")
    # pylint: disable=protected-access
    assert Database._unsaved_entries == {"einstein": "dummy"}


@pytest.mark.parametrize(
    ["label_suffix", "expected"],
    [
        [("_", LabelSuffix.ALPHA), "dummy_a"],
        [("_", LabelSuffix.CAPTIAL), "dummy_A"],
        [("_", LabelSuffix.NUMERIC), "dummy_1"],
        [(".", LabelSuffix.ALPHA), "dummy.a"],
        [(".", LabelSuffix.CAPTIAL), "dummy.A"],
        [(".", LabelSuffix.NUMERIC), "dummy.1"],
    ],
)
def test_database_disambiguate_label(
    label_suffix: Tuple[str, Callable[[str], str]], expected: str
) -> None:
    # pylint: disable=invalid-name
    """Test the `cobib.database.Database.disambiguate_label` method."""
    config.database.format.label_suffix = label_suffix

    entries = {"dummy": "test"}
    bib = Database()
    bib.update(entries)  # type: ignore

    new_label = Database().disambiguate_label("dummy")
    assert new_label == expected


def test_database_read() -> None:
    """Test the `cobib.database.Database.read` method."""
    bib = Database()
    bib.read()
    # pylint: disable=protected-access
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
        # pylint: disable=protected-access
        assert Database._unsaved_entries == {}

        with open(config.database.file, "r", encoding="utf-8") as file:
            # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
            for line, truth in zip(file, expected):
                assert line.strip() == truth.strip()
            with pytest.raises(StopIteration):
                file.__next__()
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
        # pylint: disable=protected-access
        assert Database._unsaved_entries == {}

        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    if "tags" in line:
                        assert line == "  tags: test\n"
                        # advance only the `file` iterator one step in order to catch up with the
                        # `expected` iterator
                        line = next(file)
                    assert line == truth
                with pytest.raises(StopIteration):
                    file.__next__()
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
        # pylint: disable=protected-access
        assert Database._unsaved_entries == {}

        with open(config.database.file, "r", encoding="utf-8") as file:
            with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    assert line == truth
                with pytest.raises(StopIteration):
                    file.__next__()
    finally:
        os.remove(config.database.file)
        config.database.file = EXAMPLE_LITERATURE
