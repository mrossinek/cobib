"""Tests for CoBib's Database class."""

import copy
import logging
import os
import tempfile
from shutil import copyfile

import pytest

from cobib.config import config
from cobib.database import Database, Entry

from .. import get_resource

TMPDIR = tempfile.gettempdir()
EXAMPLE_LITERATURE = get_resource("example_literature.yaml")

DUMMY_ENTRY = Entry(
    "dummy",
    {
        "ENTRYTYPE": "misc",
        "ID": "dummy",
        "author": "D. Dummy",
        "title": "Something dumb",
    },
)

DUMMY_ENTRY_YAML = """---
dummy:
    ENTRYTYPE: misc
    ID: dummy
    author: D. Dummy
    title: Something dumb
...
"""


@pytest.fixture(autouse=True)
def setup():
    """Setup."""
    config.load(get_resource("debug.py"))
    yield
    Database().clear()


def test_database_singleton():
    """Test the Database is a Singleton."""
    bib = Database()
    bib2 = Database()
    assert bib is bib2


def test_database_missing_file(caplog):
    """Test exit upon missing database file."""
    config.database.file = os.path.join(TMPDIR, "cobib_test_missing_file.yaml")
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
            pytest.fail("CoBib did not exit upon encountering a missing database file!")
    finally:
        config.database.file = EXAMPLE_LITERATURE


def test_database_update():
    """Test Database update method."""
    entries = {"dummy1": "test1", "dummy2": "test2", "dummy3": "test3"}
    bib = Database()
    bib.update(entries)
    # pylint: disable=protected-access
    assert Database._unsaved_entries == list(entries.keys())
    for key, val in entries.items():
        assert bib[key] == val


def test_database_pop():
    """Test Database pop method."""
    entries = {"dummy1": "test1", "dummy2": "test2", "dummy3": "test3"}
    bib = Database()
    bib.update(entries)
    # pylint: disable=protected-access
    Database._unsaved_entries = []
    assert Database._unsaved_entries == []
    entry = bib.pop("dummy1")
    assert entry == "test1"
    assert "dummy1" not in bib.keys()
    assert Database._unsaved_entries == ["dummy1"]


def test_database_read():
    """Test Database read method."""
    bib = Database()
    bib.read()
    # pylint: disable=protected-access
    assert Database._unsaved_entries == []
    assert list(bib.keys()) == ["einstein", "latexcompanion", "knuthwebsite"]


def test_database_save_add():
    """Test Database save method after addition."""
    # prepare temporary database
    config.database.file = os.path.join(TMPDIR, "cobib_test_database_file.yaml")
    copyfile(EXAMPLE_LITERATURE, config.database.file)

    # initialize database
    bib = Database()
    bib.read()
    bib.update({"dummy": DUMMY_ENTRY})
    bib.save()

    expected = []
    with open(EXAMPLE_LITERATURE, "r") as file:
        expected.extend(file.readlines())
    expected.extend(DUMMY_ENTRY_YAML.split("\n"))

    try:
        # pylint: disable=protected-access
        assert Database._unsaved_entries == []

        with open(config.database.file, "r") as file:
            # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
            for line, truth in zip(file, expected):
                assert line.strip() == truth.strip()
            with pytest.raises(StopIteration):
                file.__next__()
    finally:
        os.remove(config.database.file)
        config.database.file = EXAMPLE_LITERATURE


def test_database_save_modify():
    """Test Database save method after modification."""
    # prepare temporary database
    config.database.file = os.path.join(TMPDIR, "cobib_test_database_file.yaml")
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
        assert Database._unsaved_entries == []

        with open(config.database.file, "r") as file:
            with open(EXAMPLE_LITERATURE, "r") as expected:
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


def test_database_save_delete():
    """Test Database save method after deletion."""
    # prepare temporary database
    config.database.file = os.path.join(TMPDIR, "cobib_test_database_file.yaml")
    copyfile(EXAMPLE_LITERATURE, config.database.file)

    # initialize database
    bib = Database()
    bib.read()
    bib.pop("knuthwebsite")
    bib.save()

    try:
        # pylint: disable=protected-access
        assert Database._unsaved_entries == []

        with open(config.database.file, "r") as file:
            with open(EXAMPLE_LITERATURE, "r") as expected:
                # NOTE: do NOT use zip_longest to omit last entries (for testing simplicity)
                for line, truth in zip(file, expected):
                    assert line == truth
                with pytest.raises(StopIteration):
                    file.__next__()
    finally:
        os.remove(config.database.file)
        config.database.file = EXAMPLE_LITERATURE
