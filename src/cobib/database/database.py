"""coBib's Database class."""

from __future__ import annotations

import logging
import re
import sys
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, List, Optional, cast

from cobib.config import config
from cobib.utils.rel_path import RelPath

if TYPE_CHECKING:
    import cobib.database

LOGGER = logging.getLogger(__name__)


# TODO: once Python 3.9 becomes the default, OrderedDict can be properly sub-typed
class Database(OrderedDict):  # type: ignore
    """coBib's Database class is a runtime interface to the plain-test YAML file.

    This class is a *singleton*.
    Thus, accessing `cobib.database.Database` will always yield the identical instance at runtime.
    This ensures data consistency during all operations on the database.
    """

    _instance: Optional[Database] = None
    """The singleton instance of this class."""

    _unsaved_entries: Dict[str, Optional[str]] = {}
    """A dictionary of changed entries which have not been written to the database file, yet.
    The keys are the entry labels. If it the entry was removed, the value of this key is `None`.
    Otherwise it is set to the label of the changed entry (which may be different from the previous
    label, indicating a renaming of the entry)."""

    def __new__(cls) -> Database:
        """Singleton constructor.

        This method gets called when accessing `Database` and enforces the singleton pattern
        implemented by this class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._unsaved_entries = {}
        if not cls._instance and not cls._unsaved_entries:
            cls.read()
        return cls._instance

    def update(self, new_entries: Dict[str, cobib.database.Entry]) -> None:  # type: ignore
        """Updates the database with the given dictionary of entries.

        This function wraps `OrderedDict.update` and adds the labels of the changed entries to the
        dictionary of unsaved entries (`Database._unsaved_entries`). This will minimize IO access by
        only actually writing the unsaved entries in batches.

        Args:
            new_entries: the dictionary of labels mapping to entries which are to be written to the
                database.
        """
        for label in new_entries.keys():
            LOGGER.debug("Updating entry %s", label)
            Database._unsaved_entries[label] = label
        super().update(new_entries)

    def pop(self, label: str) -> cobib.database.Entry:  # type: ignore
        """Pops the entry pointed to by the given label.

        This function wraps `OrderedDict.pop` and adds the removed labels to the unsaved entries
        (`Database._unsaved_entries`). This will minimize IO access by only actually writing the
        unsaved entries in batches.

        Args:
            label: the label of the entry to be removed.

        Returns:
            The entry pointed to by the given label.
        """
        entry: cobib.database.Entry = super().pop(label)
        LOGGER.debug("Removing entry: %s", label)
        Database._unsaved_entries[label] = None
        return entry

    def rename(self, old_label: str, new_label: str) -> None:  # pylint: disable=no-self-use
        """Renames an entry label.

        This function performs no actual changes to the database. It merely registers a rename
        operation in `Database._unsaved_entries`.

        Args:
            old_label: the previous label.
            new_label: the new label.
        """
        LOGGER.debug("Renaming entry '%s' to '%s'.", old_label, new_label)
        Database._unsaved_entries[old_label] = new_label

    def disambiguate_label(self, label: str) -> str:
        """Disambiguate a given label to ensure it becomes unique.

        This function ensures that a label is unique by appending a configurable suffix to a label
        if it is already present in the database at runtime.

        Args:
            label: the label which to disambiguate.

        Returns:
            A unique label.
        """
        if label not in self.keys():
            return label

        LOGGER.warning("Label '%s' already exists in database. Running disambiguation.", label)
        separator, enumerator = config.database.format.label_suffix
        offset = 0
        while True:
            offset += 1
            new_label: str = label + separator + enumerator(offset)
            if new_label not in self.keys():
                LOGGER.info("Found new unique label: %s", new_label)
                return new_label

    @classmethod
    def read(cls) -> None:
        """Reads the database file.

        The YAML database file pointed to by the configuration file is read in and parsed.
        This uses `cobib.parsers.YAMLParser` to parse the data.
        This function clears the contents of the singleton `Database` instance and resets
        `Database._unsaved_entries` to an empty dictionary. Thus, a call to this function
        *irreversibly* synchronizes the state of the runtime `Database` instance to the actually
        written contents of the database file on disc.
        """
        if cls._instance is None:
            cls()
            return
        _instance = cls._instance

        file = RelPath(config.database.file).path
        try:
            LOGGER.info("Loading database file: %s", file)
            # pylint: disable=import-outside-toplevel
            from cobib.parsers.yaml import YAMLParser

            _instance.clear()
            _instance.update(YAMLParser().parse(file))
        except FileNotFoundError:
            LOGGER.critical("The database file %s does not exist! Please run `cobib init`!", file)
            sys.exit(1)

        cls._unsaved_entries.clear()

    @classmethod
    def save(cls) -> None:
        """Saves all unsaved entries.

        This uses `cobib.parsers.YAMLParser` to save all entries in `Database._unsaved_entries` to
        disc. In doing so, this function preserves the order of the entries in the database file by
        overwriting changed entries in-place and appending new entries to the end of the file.

        The method of determining whether an entry was added, changed or removed is the following:
        1. we read in the current database as written to disc.
        2. we iterate all lines and determine the label of the entry we are currently on.
        3. if this label is not in `Database._unsaved_entries` we continue.
        4. Otherwise we query the runtime `Database` instance for the new contents of the unsaved
           (and therefore changed) entry and remove the label from `Database._unsaved_entries`.
        5. Using `Entry.save` and a `cobib.parsers.YAMLParser` we overwrite the previous lines of
           the changed entry.
        6. Finally, all labels still left in `Database._unsaved_entries` are newly added entries and
           can simply be appended to the file.

        In order to optimize performance and IO access, all of the above is done with a single call
        to `write`.
        """
        if cls._instance is None:
            cls()
        _instance = cast(Database, cls._instance)

        # pylint: disable=import-outside-toplevel
        from cobib.parsers.yaml import YAMLParser

        yml = YAMLParser()

        file = RelPath(config.database.file).path
        with open(file, "r", encoding="utf-8") as bib:
            lines = bib.readlines()

        label_regex = re.compile(r"^([^:]+):$")

        overwrite = False
        cur_label: str = ""
        buffer: List[str] = []
        for line in lines:
            try:
                matches = label_regex.match(line)
                if matches is None:
                    raise AttributeError
                new_label = matches.groups()[0]
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

                new_label = cls._unsaved_entries.pop(cur_label)  # type: ignore
                entry = _instance.get(new_label, None)
                if entry:
                    LOGGER.debug('Writing modified entry "%s".', new_label)
                    entry_str = entry.save(parser=yml)
                    buffer.append("\n".join(entry_str.split("\n")[1:]))
                else:
                    # Entry has been deleted. Pop the previous `---` line.
                    LOGGER.debug('Deleting entry "%s".', new_label)
                    buffer.pop()
                # we pop `new_label` too, because in case of a rename it differs from `cur_label`
                cls._unsaved_entries.pop(new_label, None)
            elif not overwrite:
                # keep previous line
                buffer.append(line)

        if cls._unsaved_entries:
            for label in cls._unsaved_entries.copy().values():
                if label is None:
                    # should never occur but we avoid a type exception
                    continue
                LOGGER.debug('Adding new entry "%s".', label)
                entry_str = _instance[label].save(parser=yml)
                buffer.append(entry_str)
                cls._unsaved_entries.pop(label)

        with open(file, "w", encoding="utf-8") as bib:
            for line in buffer:
                bib.write(line)
