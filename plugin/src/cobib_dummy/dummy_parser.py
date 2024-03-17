"""A dummy parser."""

from __future__ import annotations

from typing_extensions import override

from cobib.database import Entry
from cobib.parsers.base_parser import Parser


class DummyParser(Parser):
    """A dummy parser."""

    @override
    def parse(self, string: str) -> dict[str, Entry]:
        print("DummyParser.parse")
        return {}

    @override
    def dump(self, entry: Entry) -> str | None:
        print("DummyParser.dump")
        return None
