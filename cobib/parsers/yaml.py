"""YAML Parser."""

from collections import OrderedDict
import io
import logging

from pathlib import Path
from ruamel import yaml

from cobib.database import Entry
from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class YAMLParser(Parser):
    """The YAML Parser."""

    name = 'yaml'

    class YamlDumper(yaml.YAML):
        """Wrapper class for YAML dumping."""

        # pylint: disable=arguments-differ,inconsistent-return-statements
        def dump(self, data, stream=None, **kw):
            # pdoc will inherit the docstring from the base class
            # noqa: D102
            inefficient = False
            if stream is None:
                inefficient = True
                stream = yaml.compat.StringIO()
            yaml.YAML.dump(self, data, stream, **kw)
            if inefficient:
                return stream.getvalue()

    def parse(self, string):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        bib = OrderedDict()
        LOGGER.debug('Loading YAML data from file: %s.', string)
        try:
            stream = io.StringIO(Path(string))
        except TypeError:
            try:
                stream = open(string, 'r')
            except FileNotFoundError as exc:
                raise exc
        for entry in yaml.safe_load_all(stream):
            for label, data in entry.items():
                bib[label] = Entry(label, data)
        stream.close()
        return bib

    def dump(self, entry):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        yml = self.YamlDumper()
        yml.explicit_start = True
        yml.explicit_end = True
        LOGGER.debug('Converting entry %s to YAML format.', entry.label)
        return yml.dump({entry.label: dict(sorted(entry.data.items()))})
