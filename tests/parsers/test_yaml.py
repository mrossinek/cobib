"""Tests for coBib's YAMLParser."""
# pylint: disable=unused-argument

import tempfile
from typing import Dict, Optional, cast

import pytest

from cobib.config import Event, config
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

    @pytest.mark.parametrize("use_c_lib_yaml", [False, True])
    def test_from_yaml_file(self, use_c_lib_yaml: bool) -> None:
        """Test parsing a yaml file.

        Args:
            use_c_lib_yaml: the configuration setting.
        """
        try:
            config.parsers.yaml.use_c_lib_yaml = use_c_lib_yaml
            reference = self.EXAMPLE_ENTRY_DICT.copy()
            entries = YAMLParser().parse(self.EXAMPLE_YAML_FILE)
            entry = list(entries.values())[0]
            assert entry.data == reference
        finally:
            config.defaults()

    def test_warn_duplicate_label(self, caplog: pytest.LogCaptureFixture) -> None:
        """Tests a warning is logged for duplicate labels.

        Args:
            caplog: the built-in pytest fixture.
        """
        with tempfile.NamedTemporaryFile("w") as file:
            with open(self.EXAMPLE_YAML_FILE, "r", encoding="utf-8") as existing:
                file.writelines(existing.readlines())
            with open(self.EXAMPLE_YAML_FILE, "r", encoding="utf-8") as existing:
                file.writelines(existing.readlines())
            file.flush()
            _ = YAMLParser().parse(file.name)
        assert (
            "cobib.parsers.yaml",
            30,
            "An entry with label 'Cao_2019' was already encountered earlier on in the YAML file! "
            "Please check the file manually as this cannot be resolved automatically by coBib.",
        ) in caplog.record_tuples

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
