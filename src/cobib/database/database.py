"""coBib's Database class."""

from __future__ import annotations

import logging
import pickle
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from cobib.config import config
from cobib.utils.rel_path import RelPath

if TYPE_CHECKING:
    import cobib.database

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


# TODO: once Python 3.9 becomes the default, OrderedDict can be properly sub-typed
class Database(OrderedDict):  # type: ignore
    """coBib's Database class is a runtime interface to the plain-test YAML file.

    This class is a *singleton*.
    Thus, accessing `cobib.database.Database` will always yield the identical instance at runtime.
    This ensures data consistency during all operations on the database.
    """

    _instance: Database | None = None
    """The singleton instance of this class."""

    _unsaved_entries: ClassVar[dict[str, str | None]] = {}
    """A dictionary of changed entries which have not been written to the database file, yet.
    The keys are the entry labels. If it the entry was removed, the value of this key is `None`.
    Otherwise it is set to the label of the changed entry (which may be different from the previous
    label, indicating a renaming of the entry)."""

    _read: bool = False
    """Indicates whether the database has already been read. This state is purely used to avoid an
    endless recursion during the class construction. If this state if `False`, the `__new__` method
    will automatically call `read`. The `read` method then immediately sets this flag to `True`,
    preventing further recursion. This is especially important when dealing with the separate call
    to `read_cache`."""

    def __new__(cls, *, bypass_cache: bool = False) -> Database:
        """Singleton constructor.

        This method gets called when accessing `Database` and enforces the singleton pattern
        implemented by this class.

        Args:
            bypass_cache: whether or not to try reading the cache. Set this to `True` to bypass the
                cache no matter its age or the user configuration.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._unsaved_entries = {}
        if not cls._read:
            cls.read(bypass_cache=bypass_cache)
        return cls._instance

    def update(self, new_entries: dict[str, cobib.database.Entry]) -> None:  # type: ignore
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

    def rename(self, old_label: str, new_label: str) -> None:
        """Renames an entry label.

        This function performs no actual changes to the database. It merely registers a rename
        operation in `Database._unsaved_entries`.

        Args:
            old_label: the previous label.
            new_label: the new label.
        """
        LOGGER.debug("Renaming entry '%s' to '%s'.", old_label, new_label)
        Database._unsaved_entries[old_label] = new_label
        if new_label != old_label:
            # NOTE: this is not technically needed but the rename method is exploited during
            # database linting with "fake" renames in order to register entries for re-writing
            # during saving
            super().pop(old_label)

    def disambiguate_label(self, label: str, entry: cobib.database.Entry) -> str:
        """Disambiguate a given label to ensure it becomes unique.

        This function ensures that a label is unique by appending a configurable suffix to a label
        if it is already present in the database at runtime.

        Args:
            label: the label which to disambiguate.
            entry: the `Entry` to which this label belongs.

        Returns:
            A unique label.
        """
        if label not in self.keys():
            LOGGER.info("The label '%s' does not yet exist in the runtime database.", label)
            return label

        if self[label] == entry:
            LOGGER.log(
                35,
                "Even though the label '%s' already exists in the runtime database, the entry is "
                "identical and, thus, no further disambiguation is necessary.",
                label,
            )
            return label

        LOGGER.warning("The label '%s' already exists in database. Running disambiguation.", label)
        separator, enumerator = config.database.format.label_suffix
        offset = 0
        while True:
            offset += 1
            new_label: str = label + separator + enumerator(offset)  # type: ignore[operator]
            if new_label not in self.keys():
                LOGGER.info("Found new unique label: %s", new_label)
                return new_label
            LOGGER.log(
                35,
                "The label '%s' also already exists in the database. You are seeing this because "
                "you are running a disambiguation of the label '%s'. You may want to check whether "
                "these two entries are related and (if so) edit or merge them manually. For more "
                "information see also: https://gitlab.com/cobib/cobib/-/issues/121",
                new_label,
                label,
            )

    @classmethod
    def reset(cls) -> None:
        """Resets the database.

        This clears the contents of the singleton instance and resets the `_read` class attribute.
        """
        if cls._instance is not None:
            cls._instance.clear()
        cls._read = False

    @classmethod
    def read(cls, *, bypass_cache: bool = False) -> None:
        """Reads the database file.

        The YAML database file pointed to by the configuration file is read in and parsed.
        This uses `cobib.parsers.YAMLParser` to parse the data.
        This function clears the contents of the singleton `Database` instance and resets
        `Database._unsaved_entries` to an empty dictionary. Thus, a call to this function
        *irreversibly* synchronizes the state of the runtime `Database` instance to the actually
        written contents of the database file on disc.

        Args:
            bypass_cache: whether or not to try reading the cache. Set this to `True` to bypass the
                cache no matter its age or the user configuration.
        """
        if cls._instance is None:
            cls(bypass_cache=bypass_cache)
            return
        _instance = cls._instance

        try:
            if bypass_cache:
                raise CacheError("Bypassing the cache.")
            Database.read_cache()
        except CacheError as exc:
            LOGGER.log(
                exc.log_level, "Encountered the following exception during cache lookup: '%s'", exc
            )

            file = RelPath(config.database.file).path
            try:
                LOGGER.info("Loading database file: %s", file)

                from cobib.parsers.yaml import YAMLParser

                cls._read = True
                _instance.clear()
                _instance.update(YAMLParser().parse(file))
            except FileNotFoundError:
                LOGGER.critical(
                    "The database file %s does not exist! Please run `cobib init`!", file
                )
                sys.exit(1)

            Database.save_cache()

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

        from cobib.parsers.yaml import YAMLParser

        yml = YAMLParser()

        file = RelPath(config.database.file).path
        with open(file, "r", encoding="utf-8") as bib:
            lines = bib.readlines()

        label_regex = re.compile(r"^([^:]+):$")

        overwrite = False
        cur_label: str = ""
        buffer: list[str] = []
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

                new_label = cls._unsaved_entries.pop(cur_label)
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
                if new_label is not None:
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

        Database.save_cache()

    @staticmethod
    def _get_cache_file() -> Path | None:
        """Returns the full path to the cache file for the current database file.

        Note, that this respects the `config.database.cache` and `config.database.file` settings.
        If the former is set to `None`, this method will return `None`, indicating that caching is
        disabled. The `config.database.file` setting is used to determine a unique name for the
        caching filename, simply by replacing all path separators by `%2f` (the ASCII hex code for
        the `/` symbol).


        """
        if config.database.cache is None:
            return None

        cache_location = RelPath(config.database.cache).path

        database_location = RelPath(config.database.file).path
        # we remove the anchor from the database path in order to get rid of any drive letter
        # (Windows) and root node which we do not want to include in the caching filename
        database_anchor = database_location.anchor
        database_relative = database_location.relative_to(database_anchor)
        # we can now join the parts of this relative path to form a new unique filename
        file_name = "%2f".join(database_relative.parts)

        cache_file = (cache_location / file_name).with_suffix(".pickle")
        return cache_file

    @staticmethod
    def _is_cache_outdated(cache_file: Path) -> bool:
        """Compares the age of the cache file with the database file itself.

        Args:
            cache_file: the full path to the cache file for the current database file.

        Returns:
            `True` if the cache file is outdated compared to the database file, `False` otherwise.

        Raises:
            FileNotFoundError: if the cache file does not exist.
        """
        if not cache_file.exists():
            raise FileNotFoundError

        database_location = RelPath(config.database.file).path
        cache_age = cache_file.stat().st_mtime
        database_age = database_location.stat().st_mtime

        return cache_age < database_age

    @classmethod
    def read_cache(cls) -> None:
        """Reads the database from a cache.

        Raises:
            CacheError: if caching is disable via `cobib.config.config.DatabaseConfig.cache`.
            CacheError: if the current database has not been cached yet.
            CacheError: if the cached database is older than the last modification time of the
                database file itself, indicating that the cache is outdated.
        """
        cache_file = cls._get_cache_file()
        if cache_file is None:
            exc = CacheError("caching is disabled via the configuration")
            exc.log_level = logging.DEBUG
            raise exc

        try:
            cache_outdated = cls._is_cache_outdated(cache_file)

            if cache_outdated:
                raise CacheError("the cached database is outdated")
        except FileNotFoundError as exc:
            raise CacheError("the database has not been cached yet") from exc

        LOGGER.debug("Reading the cached database from %s", str(cache_file))

        cls._read = True
        with open(cache_file, "rb") as cache:
            cast(Database, cls._instance).update(pickle.load(cache))

    @classmethod
    def save_cache(cls) -> None:
        """Saves the current database to a cache.

        This method does nothing, if the cache is already newer than the last modification time of
        the database file itself.
        """
        cache_file = cls._get_cache_file()
        if cache_file is None:
            return

        LOGGER.debug("Caching the database in %s", str(cache_file))

        try:
            cache_outdated = cls._is_cache_outdated(cache_file)
            if not cache_outdated:
                LOGGER.info("The cache is already up-to-date")
                return
        except FileNotFoundError:
            cache_file.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_file, "wb") as cache:
            pickle.dump(cls._instance, cache)


class CacheError(Exception):
    """An error class used to handle cache events."""

    log_level: int = 35
    """The logging level at which to log this exception when it gets caught."""
