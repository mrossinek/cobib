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
            prog="dummy", description="Dummy importer parser.", exit_on_error=True
        )
        cls.argparser = parser

    @override
    async def fetch(self) -> list[Entry]:
        print("DummyImporter.fetch")
        return []
