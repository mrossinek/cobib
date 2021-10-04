"""Tests for coBib's YAMLParser."""
# pylint: disable=no-self-use,unused-argument

from typing import Dict, Optional, cast

import pytest

from cobib.config import Event
from cobib.database import Entry
from cobib.parsers import YAMLParser

from .parser_test import ParserTest


class TestYAMLParser(ParserTest):
    """Tests for coBib's YAMLParser."""

    def test_to_yaml(self) -> None:
        """Test to yaml conversion."""
        entry = Entry("Cao_2019", self.EXAMPLE_ENTRY_DICT)
        yaml_str = YAMLParser().dump(entry)
        with open(self.EXAMPLE_YAML_FILE, "r", encoding="utf-8") as file:
            assert yaml_str == file.read()

    def test_from_yaml_file(self) -> None:
        """Test parsing a yaml file."""
        reference = self.EXAMPLE_ENTRY_DICT.copy()
        entries = YAMLParser().parse(self.EXAMPLE_YAML_FILE)
        entry = list(entries.values())[0]
        assert entry.data == reference

    def test_raise_missing_file(self) -> None:
        """Test assertion is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            YAMLParser().parse("test/missing_file.yaml")

    def test_event_pre_yaml_parse(self) -> None:
        """Tests the PreYAMLParse event."""

        @Event.PreYAMLParse.subscribe
        def hook(string: str) -> Optional[str]:
            return self.EXAMPLE_YAML_FILE

        assert Event.PreYAMLParse.validate()

        reference = self.EXAMPLE_ENTRY_DICT.copy()
        entries = YAMLParser().parse("Hello world!")
        entry = list(entries.values())[0]
        assert entry.data == reference

    def test_event_post_yaml_parse(self) -> None:
        """Tests the PostYAMLParse event."""

        @Event.PostYAMLParse.subscribe
        def hook(bib: Dict[str, Entry]) -> None:
            bib["Cao_2019"].data["month"] = "August"

        reference = self.EXAMPLE_ENTRY_DICT.copy()
        reference["month"] = "August"

        assert Event.PostYAMLParse.validate()

        entries = YAMLParser().parse(self.EXAMPLE_YAML_FILE)
        entry = list(entries.values())[0]
        assert entry.data == reference

    def test_event_pre_yaml_dump(self) -> None:
        """Tests the PreYAMLDump event."""

        @Event.PreYAMLDump.subscribe
        def hook(entry: Entry) -> None:
            entry.label = "Cao2019"

        assert Event.PreYAMLDump.validate()

        entry = Entry("Cao_2019", self.EXAMPLE_ENTRY_DICT.copy())
        entry_str = YAMLParser().dump(entry)
        assert cast(str, entry_str).split("\n")[1] == "Cao2019:"

    def test_event_post_yaml_dump(self) -> None:
        """Tests the PostYAMLDump event."""

        @Event.PostYAMLDump.subscribe
        def hook(string: str) -> Optional[str]:
            return "Hello world!"

        assert Event.PostYAMLDump.validate()

        entry = Entry("Cao_2019", self.EXAMPLE_ENTRY_DICT.copy())
        entry_str = YAMLParser().dump(entry)
        assert entry_str == "Hello world!"
