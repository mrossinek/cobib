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

import io
import logging
import sys
from collections import OrderedDict
from pathlib import Path
from typing import IO, Dict, Optional, Union

from rich.console import Console
from rich.progress import track
from ruamel import yaml
from typing_extensions import override

from cobib.config import Event, config
from cobib.database.entry import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class YAMLParser(Parser):
    """The YAML Parser."""

    name = "yaml"

    _yaml: Optional[yaml.YAML] = None

    def __init__(self) -> None:  # pylint: disable=C0116
        # noqa: D107
        if YAMLParser._yaml is None:
            # we need to lazily construct this in order to be able to respect the config setting
            YAMLParser._yaml = yaml.YAML(typ="safe", pure=not config.parsers.yaml.use_c_lib_yaml)
            YAMLParser._yaml.explicit_start = True  # type: ignore[assignment]
            YAMLParser._yaml.explicit_end = True  # type: ignore[assignment]
            YAMLParser._yaml.default_flow_style = False

    @override
    def parse(self, string: Union[str, Path]) -> Dict[str, Entry]:
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
        for entry in track(
            self._yaml.load_all(stream),  # type: ignore[union-attr]
            description="Reading database...",
            transient=True,
            console=Console(file=sys.stderr),  # TODO: do not hard-code this
        ):
            for label, data in entry.items():
                bib[label] = Entry(label, data)
        stream.close()

        Event.PostYAMLParse.fire(bib)

        return bib

    @override
    def dump(self, entry: Entry) -> Optional[str]:
        Event.PreYAMLDump.fire(entry)

        LOGGER.debug("Converting entry %s to YAML format.", entry.label)
        stream = io.StringIO()
        self._yaml.dump(  # type: ignore[union-attr]
            {entry.label: dict(sorted(entry.data.items()))}, stream=stream
        )
        string = stream.getvalue()

        string = Event.PostYAMLDump.fire(string) or string

        return string
