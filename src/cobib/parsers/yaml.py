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
from typing import IO, Dict, Optional, Union, cast

from ruamel import yaml

from cobib.config import Event
from cobib.database import Entry

from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class YAMLParser(Parser):
    """The YAML Parser."""

    name = "yaml"

    class YamlDumper(yaml.YAML):  # type: ignore
        """Wrapper class for YAML dumping."""

        # pylint: disable=arguments-differ,inconsistent-return-statements
        def dump(self, data, stream=None, **kw) -> Optional[str]:  # type: ignore
            """A wrapper to dump as a string.

            Adapted from
            [here](https://yaml.readthedocs.io/en/latest/example.html#output-of-dump-as-a-string).
            """
            inefficient = False
            if stream is None:  # pragma: no branch
                inefficient = True
                stream = yaml.compat.StringIO()
            yaml.YAML.dump(self, data, stream, **kw)  # type: ignore
            if inefficient:
                return cast(str, stream.getvalue())
            return None  # pragma: no cover

    def parse(self, string: Union[str, Path]) -> Dict[str, Entry]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102

        string = Event.PreYAMLParse.fire(string) or string

        bib = OrderedDict()
        LOGGER.debug("Loading YAML data from file: %s.", string)
        try:
            stream: IO = io.StringIO(Path(string))  # type: ignore
        except TypeError:
            try:
                stream = open(string, "r", encoding="utf-8")  # pylint: disable=consider-using-with
            except FileNotFoundError as exc:
                raise exc
        yml = yaml.YAML(typ="safe", pure=True)  # type: ignore
        for entry in yml.load_all(stream):
            for label, data in entry.items():
                bib[label] = Entry(label, data)
        stream.close()

        Event.PostYAMLParse.fire(bib)

        return bib

    def dump(self, entry: Entry) -> Optional[str]:
        # pdoc will inherit the docstring from the base class
        # noqa: D102

        Event.PreYAMLDump.fire(entry)

        yml = self.YamlDumper()
        yml.explicit_start = True
        yml.explicit_end = True
        LOGGER.debug("Converting entry %s to YAML format.", entry.label)
        string = yml.dump({entry.label: dict(sorted(entry.data.items()))})

        string = Event.PostYAMLDump.fire(string) or string

        return string
