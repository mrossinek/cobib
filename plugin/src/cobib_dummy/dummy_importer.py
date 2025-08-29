"""A dummy importer."""

from __future__ import annotations

import argparse

from typing_extensions import override

from cobib.database import Entry
from cobib.importers.base_importer import Importer


class DummyImporter(Importer):
    """A dummy importer."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="dummy",
            description="Dummy importer parser.",
            epilog="Read cobib-dummy-importer.7 for more help.",
        )
        cls.argparser = parser

    @override
    async def fetch(self) -> list[Entry]:
        print("DummyImporter.fetch")
        return []
