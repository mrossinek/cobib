"""Database handler module."""

from collections import OrderedDict
from pathlib import Path
import logging
import os
import sys

from cobib.config import config
from cobib.parser import Entry

LOGGER = logging.getLogger(__name__)


def read_database():
    """Reads the database file.

    The YAML database file pointed to by the configuration file is read in and parsed. The data is
    stored as an OrderedDict in the global configuration object.
    """
    file = os.path.expanduser(config.database.file)
    try:
        LOGGER.info('Loading database file: %s', file)
        config.bibliography = Entry.from_yaml(Path(file))
    except AttributeError:
        LOGGER.debug('Initializing an empty database.')
        config.bibliography = OrderedDict()
    except FileNotFoundError:
        LOGGER.critical("The database file %s does not exist! Please run `cobib init`!", file)
        sys.exit(1)


def write_database(entries):
    """Writes to the database file.

    Appends the bibliographic data of the provided entries to the database file. If a label already
    exists in the database, the corresponding entry is skipped.

    Args:
        entries (list[Entry]): list of new bibliography entries

    Returns:
        A list of the actually written entries.
    """
    new_lines = []
    new_entries = []
    for label, entry in entries.items():
        if label in config.bibliography.keys():
            LOGGER.warning("Label %s already exists! Ignoring the new version.", label)
            continue
        string = entry.to_yaml()
        reduced = '\n'.join(string.splitlines())
        new_lines.append(reduced)
        new_entries.append(label)

    if new_lines:
        file = os.path.expanduser(config.database.file)
        # append new lines to the database file
        with open(file, 'a') as bib:
            for line in new_lines:
                LOGGER.debug('Appending line to database file: %s', line)
                bib.write(line+'\n')

    return new_entries
