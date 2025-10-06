"""A dummy exporter."""

from __future__ import annotations

import argparse

from typing_extensions import override

from cobib.database import Entry
from cobib.exporters.base_exporter import Exporter


class DummyExporter(Exporter):
    """A dummy exporter."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="dummy",
            description="Dummy exporter parser.",
            epilog="Read cobib-dummy-exporter.7 for more help.",
        )
        cls.argparser = parser

    @override
    def write(self, entries: list[Entry]) -> None:
        print("DummyExporter.write")
