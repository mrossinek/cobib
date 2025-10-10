"""Tests for coBib's YAMLExporter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import ExportCommand
from cobib.config import Event
from cobib.database import Database
from cobib.exporters import YAMLExporter

from .. import get_resource
from ..commands import CommandTest
from .exporter_test import ExporterTest

if TYPE_CHECKING:
    import cobib.commands

TMPDIR = Path(tempfile.gettempdir())


class TestYAMLExporter(ExporterTest):
    """Tests for coBib's YAMLExporter."""

    def test_event_pre_yaml_export(self) -> None:
        """Tests the PreYAMLExport event."""

        @Event.PreYAMLExport.subscribe
        def hook(exporter: YAMLExporter) -> None:
            exporter.exported_entries = [Database()["einstein"]]

        assert Event.PreYAMLExport.validate()

        path = str(TMPDIR / "cobib_test_export.yaml")
        YAMLExporter(path).write([])

        TestYAMLExport._assert(["-s", "--yaml", path, "--", "einstein"])

    def test_event_post_yaml_export(self) -> None:
        """Tests the PostYAMLExport event."""
        path = TMPDIR / "cobib_test_export.yaml"

        @Event.PostYAMLExport.subscribe
        def hook(exporter: YAMLExporter) -> None:
            exporter.largs.file.write("test")

        assert Event.PostYAMLExport.validate()

        YAMLExporter(str(path)).write([Database()["einstein"]])

        try:
            assert open(path, "r", encoding="utf-8").readlines()[-1] == "test"
        finally:
            path.unlink(missing_ok=True)


class TestYAMLExport(CommandTest):
    """Tests for coBib's YAMLExporter via the ExportCommand."""

    @override
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return ExportCommand

    @staticmethod
    def _assert(args: list[str]) -> None:
        """Assertion utility method for YAML output.

        Args:
            args: the arguments which were passed to the command.
        """
        try:
            with open(TMPDIR / "cobib_test_export.yaml", "r", encoding="utf-8") as file:
                with open(
                    get_resource("example_literature.yaml"), "r", encoding="utf-8"
                ) as expected:
                    # NOTE: do NOT use zip_longest to omit later entries
                    for line, truth in zip(file, expected):
                        if truth[0] == "%":
                            # ignore comments
                            continue
                        assert line == truth
                    if "-s" in args:
                        with pytest.raises(StopIteration):
                            next(file)
        finally:
            # clean up file system
            (TMPDIR / "cobib_test_export.yaml").unlink(missing_ok=True)

    @pytest.mark.parametrize(
        ["args"],
        [
            [["--yaml", "--", str(TMPDIR / "cobib_test_export.yaml")]],
            [
                [
                    "--yaml",
                    "--",
                    str(TMPDIR / "cobib_test_export.yaml"),
                    "--",
                    "++label",
                    "einstein",
                ]
            ],
            [["--yaml", str(TMPDIR / "cobib_test_export.yaml"), "-s", "--", "einstein"]],
            # the following limit test works only if "einstein" is the first entry in the database
            [["--yaml", str(TMPDIR / "cobib_test_export.yaml"), "--", "-l", "1"]],
        ],
    )
    def test_command(self, setup: Any, args: list[str]) -> None:
        """Test exporting to YAML via the ExportCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: the arguments to pass to the command.
        """
        ExportCommand(*args).execute()
        self._assert(args)
