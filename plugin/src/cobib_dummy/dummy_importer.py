"""A dummy importer."""

from __future__ import annotations

from typing_extensions import override

from cobib.database import Entry
from cobib.importers.base_importer import ArgumentParser, Importer


class DummyImporter(Importer):
    """A dummy importer."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="dummy", description="Dummy importer parser.")
        cls.argparser = parser

    @override
    async def fetch(self) -> list[Entry]:
        print("DummyImporter.fetch")
        return []
