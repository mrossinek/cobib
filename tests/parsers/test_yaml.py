"""Tests for coBib's YAMLParser."""
# pylint: disable=no-self-use,unused-argument

import pytest

from cobib import parsers
from cobib.database import Entry

from .parser_test import ParserTest


class TestYAMLParser(ParserTest):
    """Tests for coBib's YAMLParser."""

    def test_to_yaml(self) -> None:
        """Test to yaml conversion."""
        entry = Entry("Cao_2019", self.EXAMPLE_ENTRY_DICT)
        yaml_str = parsers.YAMLParser().dump(entry)
        with open(self.EXAMPLE_YAML_FILE, "r") as file:
            assert yaml_str == file.read()

    def test_from_yaml_file(self) -> None:
        """Test parsing a yaml file."""
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        # with open(EXAMPLE_YAML_FILE, 'r') as yaml_file:
        entries = parsers.YAMLParser().parse(self.EXAMPLE_YAML_FILE)
        entry = list(entries.values())[0]
        assert entry.data == reference

    def test_raise_missing_file(self) -> None:
        """Test assertion is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            parsers.YAMLParser().parse("test/missing_file.yaml")
