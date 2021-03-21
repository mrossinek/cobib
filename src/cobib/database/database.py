"""coBib database module."""

import logging
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

from cobib.config import config

LOGGER = logging.getLogger(__name__)


class Database(OrderedDict):
    """coBib's database class."""

    _instance = None

    _unsaved_entries = []

    def __new__(cls):
        """Singleton constructor."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # store all unsaved entries in a set
            cls._unsaved_entries = []
        if not cls._instance and not cls._unsaved_entries:
            cls.read()
        return cls._instance

    def update(self, new_entries):
        """Updates the database with the given dictionary of entries."""
        for label in new_entries.keys():
            LOGGER.debug("Updating entry %s", label)
            if label in Database._unsaved_entries:
                Database._unsaved_entries.remove(label)
            Database._unsaved_entries.append(label)
        super().update(new_entries)

    def pop(self, label):
        """Pops the entry pointed to by the given label."""
        entry = super().pop(label)
        LOGGER.debug("Removing entry: %s", label)
        if label in Database._unsaved_entries:
            Database._unsaved_entries.remove(label)
        Database._unsaved_entries.append(label)
        return entry

    @classmethod
    def read(cls):
        """Reads the database file.

        The YAML database file pointed to by the configuration file is read in and parsed.
        The data is stored as an OrderedDict in the global configuration object.
        """
        file = os.path.expanduser(config.database.file)
        try:
            LOGGER.info("Loading database file: %s", file)
            # pylint: disable=import-outside-toplevel,cyclic-import
            from cobib.parsers import YAMLParser

            cls._instance.clear()
            cls._instance.update(YAMLParser().parse(Path(file)))
        except FileNotFoundError:
            LOGGER.critical("The database file %s does not exist! Please run `cobib init`!", file)
            sys.exit(1)

        cls._unsaved_entries.clear()

    @classmethod
    def save(cls):
        """Saves all unsaved entries."""
        # pylint: disable=import-outside-toplevel,cyclic-import
        from cobib.parsers import YAMLParser

        yml = YAMLParser()

        file = os.path.expanduser(config.database.file)
        with open(file, "r") as bib:
            lines = bib.readlines()

        label_regex = re.compile(r"^([^:]+):$")

        overwrite = False
        cur_label = None
        buffer = []
        for line in lines:
            try:
                new_label = label_regex.match(line).groups()[0]
                if new_label in cls._unsaved_entries:
                    LOGGER.debug('Entry "%s" found. Starting to replace lines.', new_label)
                    overwrite = True
                    cur_label = new_label
                    continue
            except AttributeError:
                pass
            if overwrite and line.startswith("..."):
                LOGGER.debug('Reached end of entry "%s".', cur_label)
                overwrite = False

                entry = cls._instance.get(cur_label, None)
                if entry:
                    LOGGER.debug('Writing modified entry "%s".', cur_label)
                    entry_str = entry.save(parser=yml)
                    buffer.append("\n".join(entry_str.split("\n")[1:]))
                else:
                    # Entry has been deleted. Pop the previous `---` line.
                    LOGGER.debug('Deleting entry "%s".', cur_label)
                    buffer.pop()
                cls._unsaved_entries.remove(cur_label)
            elif not overwrite:
                # keep previous line
                buffer.append(line)

        if cls._unsaved_entries:
            for label in cls._unsaved_entries.copy():
                LOGGER.debug('Adding new entry "%s".', label)
                entry_str = cls._instance[label].save(parser=yml)
                buffer.append(entry_str)
                cls._unsaved_entries.remove(label)

        with open(file, "w") as bib:
            for line in buffer:
                bib.write(line)
