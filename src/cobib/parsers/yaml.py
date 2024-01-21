# mypy: warn-unused-ignores=False
"""coBib's YAML parser.

This parser leverages the [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/) library to convert
between `cobib.database.Entry` instances and YAML representations of their `dict`-like data
structure.

The parser is registered under the `-y` and `--yaml` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

from __future__ import annotations

import io
import logging
import sys
from collections import OrderedDict
from pathlib import Path
from typing import IO

from rich.console import Console
from rich.progress import track
from ruamel import yaml
from typing_extensions import override

from cobib.config import Event, config
from cobib.database.author import Author
from cobib.database.entry import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class YAMLParser(Parser):
    """The YAML Parser."""

    name = "yaml"

    _yaml: yaml.YAML | None = None

    def __init__(self) -> None:
        """Initializes a YAMLParser."""
        if YAMLParser._yaml is None:
            # we need to lazily construct this in order to be able to respect the config setting
            YAMLParser._yaml = yaml.YAML(typ="safe", pure=not config.parsers.yaml.use_c_lib_yaml)
            YAMLParser._yaml.explicit_start = True  # type: ignore[assignment]
            YAMLParser._yaml.explicit_end = True  # type: ignore[assignment]
            YAMLParser._yaml.default_flow_style = False
            YAMLParser._yaml.register_class(Author)

    @override
    def parse(self, string: str | Path) -> dict[str, Entry]:
        string = Event.PreYAMLParse.fire(string) or string

        try:
            LOGGER.debug("Attempting to load YAML data from file: %s.", string)
            stream = open(string, "r", encoding="utf-8")
            bib = self._load_all(stream)
            stream.close()
        except (OSError, FileNotFoundError) as exc:
            try:
                LOGGER.debug("Attempting to load YAML data from string: %s.", string)
                stream = io.StringIO(string)  # type: ignore[arg-type]
                bib = self._load_all(stream)
                stream.close()
            except (TypeError, AttributeError):
                raise exc

        Event.PostYAMLParse.fire(bib)

        return bib

    def _load_all(self, stream: IO) -> dict[str, Entry]:  # type: ignore[type-arg]
        bib: dict[str, Entry] = OrderedDict()

        for entry in track(
            self._yaml.load_all(stream),  # type: ignore[union-attr]
            description="Reading database...",
            transient=True,
            console=Console(file=sys.stderr),
        ):
            for label, data in entry.items():
                actual_entry = Entry(label, data)
                if actual_entry.label in bib.keys():
                    LOGGER.warning(
                        "An entry with label '%s' was already encountered earlier on in the YAML "
                        "file! Please check the file manually as this cannot be resolved "
                        "automatically by coBib.",
                        actual_entry.label,
                    )
                bib[actual_entry.label] = actual_entry

        return bib

    @override
    def dump(self, entry: Entry) -> str | None:
        Event.PreYAMLDump.fire(entry)

        LOGGER.debug("Converting entry %s to YAML format.", entry.label)
        stream = io.StringIO()
        self._yaml.dump(  # type: ignore[union-attr]
            {entry.label: dict(sorted(entry.data.items()))}, stream=stream
        )
        string = stream.getvalue()

        string = Event.PostYAMLDump.fire(string) or string

        return string
