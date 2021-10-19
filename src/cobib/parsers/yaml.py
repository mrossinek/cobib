"""coBib's YAML parser.

This parser leverages the [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/) library to convert
between `cobib.database.Entry` instances and YAML representations of their `dict`-like data
structure.

The parser is registered under the `-y` and `--yaml` command-line arguments of the
`cobib.commands.add.AddCommand`.

The following documentation is mostly inherited from the abstract interface
`cobib.parsers.base_parser`.
"""

import io
import logging
from collections import OrderedDict
from pathlib import Path
from typing import IO, Dict, Optional, Union

from ruamel import yaml

from cobib.config import Event, config
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class YAMLParser(Parser):
    """The YAML Parser."""

    name = "yaml"

    _yaml = yaml.YAML(pure=config.parsers.yaml.use_c_lib_yaml)  # type: ignore[attr-defined]
    _yaml.explicit_start = True
    _yaml.explicit_end = True

    def parse(self, string: Union[str, Path]) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102

        string = Event.PreYAMLParse.fire(string) or string

        bib = OrderedDict()
        LOGGER.debug("Loading YAML data from file: %s.", string)
        try:
            stream: IO = io.StringIO(Path(string))  # type: ignore[arg-type,type-arg]
        except TypeError:
            try:
                stream = open(string, "r", encoding="utf-8")  # pylint: disable=consider-using-with
            except FileNotFoundError as exc:
                raise exc
        for entry in self._yaml.load_all(stream):
            for label, data in entry.items():
                bib[label] = Entry(label, data)
        stream.close()

        Event.PostYAMLParse.fire(bib)

        return bib

    def dump(self, entry: Entry) -> Optional[str]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102

        Event.PreYAMLDump.fire(entry)

        LOGGER.debug("Converting entry %s to YAML format.", entry.label)
        stream = io.StringIO()
        self._yaml.dump({entry.label: dict(sorted(entry.data.items()))}, stream=stream)
        string = stream.getvalue()

        string = Event.PostYAMLDump.fire(string) or string

        return string
