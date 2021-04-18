"""Tests for coBib's path utility."""

from pathlib import Path

from cobib.utils.rel_path import RelPath


def test_relative_path() -> None:
    """Test a path which is relative to the user's home directory."""
    path = Path.home() / "dummy.txt"
    rel_path = RelPath(path)

    # the string is relative
    assert str(rel_path) == "~/dummy.txt"
    # the path property is fully-resolved
    assert rel_path.path == path
    # getting a Path-property resolves the path first
    assert rel_path.parent == Path.home()


def test_absolute_path() -> None:
    """Test a path which is not relative to the user's home directory and therefore absolute."""
    path = Path("/tmp/dummy.txt")
    abs_path = RelPath(path)

    # the string is relative
    assert str(abs_path) == "/tmp/dummy.txt"
    # the path property is fully-resolved
    assert abs_path.path == path
    # getting a Path-property resolves the path first
    assert abs_path.parent == Path("/tmp")
