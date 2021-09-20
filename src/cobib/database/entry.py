"""coBib's Entry class."""

from __future__ import annotations

import logging
import re
import subprocess
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from pylatexenc.latexencode import UnicodeToLatexEncoder

from cobib.config import config
from cobib.utils.rel_path import RelPath

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.parsers


class Entry:
    """coBib's bibliographic entry.

    coBib's `Database` stores the bibliographic information in entries which are instances of this
    class. This only contains a `label` which is a string used as a key to associate this entry as
    well as a free-form `data` dictionary, which can contain arbitrary key-value pairs.
    One field will *always* be present in the `data` dictionary:
    * `ENTRYTYPE`: which specifies the BibLaTex type of the entry.

    Only through the context imposed by BibLaTex will the other `data` fields be interpreted.

    However, some keys are exposed as properties in a special format to provide easy access to these
    meta-data fields not typically used by BibLaTex itself.

    Besides being a data container, this class also provides some utilities for data manipulation
    and querying.
    """

    def __init__(self, label: str, data: Dict[str, Any]) -> None:
        """Initializes a new Entry.

        Args:
            label: the label associated with this entry in the `Database`.
            data: the actual bibliographic data stored as a dictionary mapping free-form field names
                (`str`) to any other data. Some fields are exposed as properties of this class for
                convenience.
        """
        LOGGER.debug("Initializing entry: %s", label)

        self._label: str = str(label)

        self.data: Dict[str, Any] = {}
        """The actual bibliographic data."""

        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif isinstance(value, str) and value.isnumeric():
                LOGGER.info(
                    "Converting field '%s' of entry '%s' to integer: %s.",
                    key,
                    label,
                    value,
                    extra={"entry": label, "field": key},
                )
                self.data[key] = int(value)
            else:
                self.data[key] = value

        if "ID" in self.data:
            self.data.pop("ID")
            LOGGER.info(
                "The field '%s' of entry '%s' is no longer required. It will be inferred from the "
                "entry label.",
                "ID",
                label,
                extra={"entry": label, "field": "ID"},
            )

    def __eq__(self, other: object) -> bool:
        """Checks equality of two entries."""
        if not isinstance(other, Entry):
            return False
        return self.label == other.label and self.data == other.data

    @property
    def label(self) -> str:
        """The `Database` label of this entry."""
        return self._label

    @label.setter
    def label(self, label: str) -> None:
        """Sets the `Database` label of this entry.

        Args:
            label: the label of this entry.
        """
        LOGGER.debug("Changing the label '%s' to '%s'.", self.label, label)
        self._label = str(label)

    @property
    def tags(self) -> List[str]:
        """The tags of this entry."""
        return self.data.get("tags", [])

    @tags.setter
    def tags(self, tags: Union[str, List[str]]) -> None:
        """Sets the tags of this entry.

        Args:
            tags: a single or list of tags.
        """
        if isinstance(tags, list):
            self.data["tags"] = tags
        else:
            self.data["tags"] = tags.split(config.database.stringify.list_separator.tags)
            if len(self.data["tags"]) > 1:
                LOGGER.info(
                    "Converted the field '%s' of entry '%s' to a list. You can consider storing it "
                    "as such directly.",
                    "tags",
                    self.label,
                    extra={"entry": self.label, "field": "tags"},
                )
        LOGGER.debug("Adding the tags '%s' to '%s'.", self.data["tags"], self.label)

    @property
    def file(self) -> List[str]:
        # noqa: D402 (we skip this error because file(s) raises a false negative)
        """The associated file(s) of this entry.

        The setter of this property will convert the strings to paths relative to the user's home
        directory. Internally, this field will always be stored as a list.
        """
        return self.data.get("file", [])

    @file.setter
    def file(self, file: Union[str, List[str]]) -> None:
        # noqa: D402 (we skip this error because file(s) raises a false negative)
        """Sets the associated file(s) of this entry.

        Args:
            file: can be either a single path (`str`) or a list thereof. In either case, the strings
                will be converted to paths relative to the user's home directory. Internally, this
                field will always be stored as a list.
        """
        if isinstance(file, list):
            paths = [RelPath(f) for f in file]
        else:
            paths = [RelPath(f) for f in file.split(config.database.stringify.list_separator.file)]
            if len(paths) > 1:
                LOGGER.info(
                    "Converted the field '%s' of entry '%s' to a list. You can consider storing it "
                    "as such directly.",
                    "file",
                    self.label,
                    extra={"entry": self.label, "field": "file"},
                )
        self.data["file"] = [str(p) for p in paths]
        LOGGER.debug("Adding '%s' as the file to '%s'.", self.data["file"], self.label)

    @property
    def url(self) -> List[str]:
        """The associated URL(s) of this entry."""
        return self.data.get("url", [])

    @url.setter
    def url(self, url: Union[str, List[str]]) -> None:
        """Sets the associated URL(s) of this entry.

        Args:
            url: can be either a single URL (`str`) or a list thereof. Internally, this field will
            always be stored as a list.
        """
        if isinstance(url, list):
            self.data["url"] = url
        else:
            self.data["url"] = url.split(config.database.stringify.list_separator.url)
            if len(self.data["url"]) > 1:
                LOGGER.info(
                    "Converted the field '%s' of entry '%s' to a list. You can consider storing it "
                    "as such directly.",
                    "url",
                    self.label,
                    extra={"entry": self.label, "field": "url"},
                )
        LOGGER.debug("Adding '%s' as the url to '%s'.", self.data["url"], self.label)

    @property
    def month(self) -> str:
        """Returns the month."""
        return self.data.get("month", None)

    @month.setter
    def month(self, month: Union[int, str]) -> None:
        """Sets the month."""
        months = [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ]
        if month in months:
            self.data["month"] = month
        else:
            if isinstance(month, int):
                self.data["month"] = months[month - 1]
            elif isinstance(month, str):
                if month.isnumeric():
                    self.data["month"] = months[int(month) - 1]
                else:
                    self.data["month"] = month.lower()[:3]
            LOGGER.info(
                "Converting field '%s' of entry '%s' from '%s' to '%s'.",
                "month",
                self.label,
                month,
                self.data["month"],
                extra={"entry": self.label, "field": "month"},
            )

    def stringify(self) -> Dict[str, str]:
        """Returns an identical entry to self but with all fields converted to strings.

        Returns:
            An `Entry` with purely string fields.
        """
        data = {}
        data["label"] = self.label
        for field, value in self.data.items():
            if (
                isinstance(value, list)
                and field in config["database"]["stringify"]["list_separator"].keys()
            ):
                data[field] = config["database"]["stringify"]["list_separator"][field].join(value)
            else:
                data[field] = str(value)
        return data

    def escape_special_chars(self, suppress_warnings: bool = True) -> None:
        """Escapes special characters in the bibliographic data.

        Special characters should be escaped to ensure proper rendering in LaTeX documents. This
        function leverages the existing implementation of the `pylatexenc` module to do said
        conversion. The only fields exempted from the conversion are the `file` and `url` fields of
        the `Entry.data` dictionary.

        Args:
            suppress_warnings: if True, warnings generated by the `pylatexenc` modules will be
                suppressed. This argument will be overwritten if the logging level is set to
                `logging.DEBUG`.
        """
        enc = UnicodeToLatexEncoder(
            non_ascii_only=True,
            replacement_latex_protection="braces-all",
            unknown_char_policy="keep",
            unknown_char_warning=not suppress_warnings or LOGGER.isEnabledFor(logging.DEBUG),
        )
        for key, value in self.data.items():
            if key in ("file", "url"):
                # do NOT these fields and keep any special characters
                self.data[key] = value
                continue
            if isinstance(value, str):
                self.data[key] = enc.unicode_to_latex(value)

    def save(self, parser: Optional[cobib.parsers.base_parser.Parser] = None) -> str:
        """Saves an entry using the parsers `dump` method.

        This method is mainly used by the `Database.save` method and takes care of some final
        conversions depending on the user's configuration. Applying such modifications (like e.g.
        special character escaping) only before saving ensures a consistent state of the database
        while also providing a fast startup because these conversions are prevented at that time.

        Args:
            parser: the parser instance to use for dumping. If set to `None` it will default to a
                `cobib.parsers.YAMLParser`. Supplying a ready instance can improve efficiency
                significantly while saving many entries after one another.

        Returns:
            The string-representation of this entry as produced by the provided parser.
        """
        self.escape_special_chars(config.database.format.suppress_latex_warnings)
        if parser is None:
            # pylint: disable=import-outside-toplevel,cyclic-import
            from cobib.parsers.yaml import YAMLParser

            parser = YAMLParser()
        return parser.dump(self) or ""  # `dump` may return `None`

    def matches(self, filter_: Dict[Tuple[str, bool], List[str]], or_: bool) -> bool:
        """Check whether this entry matches the supplied filter.

        coBib provides an extensive filtering implementation. The filter is specified in the form
        of a dictionary whose keys consist of pairs of `(str, bool)` entries where the string
        indicates the field to match against and the boolean whether a positive (`true`) or negative
        (`false`) match is required. The values of the dictionary must be a `List[str]`. This means
        that field types are always compared on a string-basis (this is a limitation of the targeted
        command-line interface). However, as of v3.2.0 these strings are interpreted as regex
        patterns providing the most powerful within this framework.

        Some examples:

        | `filter_`                             | `or_`    | Meaning                               |
        | ------------------------------------- | -------- | ------------------------------------- |
        | `{('year', True): ['2020']}`          | *either* | `year` contains 2020                  |
        | `{('year', False): ['2020']}`         | *either* | `year` does not contain 2020          |
        | `{('year', True): ['2020', '2021']}`  | True     | `year` contains either 2020 or 2021   |
        | `{('year', True): ['2020', '2021']}`  | False    | cannot match anything                 |
        | `{('year', False): ['2020', '2021']}` | False    | `year` contains neither 2020 nor 2021 |

        Args:
            filter_: dictionary describing the filter as explained above.
            or_ : boolean indicating whether logical OR (`true`) or AND (`false`) is used to combine
                multiple filter items.

        Returns:
            Boolean indicating whether this entry matches the filter.
        """
        LOGGER.debug("Checking whether entry %s matches.", self.label)
        match_list = []
        stringified_data = self.stringify()
        for key, values in filter_.items():
            if key[0] not in stringified_data.keys():
                match_list.append(not key[1])
                continue
            for val in values:
                if re.search(rf"{val}", stringified_data[key[0]]):
                    match_list.append(key[1])
                else:
                    match_list.append(not key[1])
        if or_:
            return any(m for m in match_list)
        return all(m for m in match_list)

    def search(self, query: str, context: int = 1, ignore_case: bool = False) -> List[List[str]]:
        """Search entry contents for the query string.

        The entry will *always* be converted to a searchable string using the
        `cobib.parsers.BibtexParser.dump` method. This text will then be search for `query` which
        will be interpreted as a regex pattern.
        If a `file` is associated with this entry, the search will try its best to recursively query
        its contents, too. However, the success of this depends highly on the configured search
        tool, `config.commands.search.grep`.

        Args:
            query: the text to search for.
            context: the number of context lines to provide for each match. This behaves similarly
                to the *Context Line Control* available for the UNIX `grep` command (`--context`).
            ignore_case: if True, the search will be case-*in*sensitive.

        Returns:
            A list of lists containing the context for each match associated with this entry.
        """
        LOGGER.debug("Searching entry %s for %s.", self.label, query)
        matches: List[List[str]] = []
        # pylint: disable=import-outside-toplevel,cyclic-import
        from cobib.parsers.bibtex import BibtexParser

        bibtex = BibtexParser().dump(self).split("\n")
        re_flags = re.IGNORECASE if ignore_case else 0
        re_compiled = re.compile(rf"{query}", flags=re_flags)
        for idx, line in enumerate(bibtex):
            if re_compiled.search(line):
                # add new match
                matches.append([])
                # upper context; (we iterate in reverse in order to ensure that we abort on the
                # first previous occurrence of the query pattern)
                for string in reversed(bibtex[max(idx - context, 0) : min(idx, len(bibtex))]):
                    if re_compiled.search(string):
                        break
                    matches[-1].insert(0, string)
                # matching line itself
                matches[-1].append(line)
                # lower context
                for string in bibtex[max(idx + 1, 0) : min(idx + context + 1, len(bibtex))]:
                    if re_compiled.search(string):
                        break
                    matches[-1].append(string)

        for file_ in self.file:
            grep_prog = config.commands.search.grep
            LOGGER.debug("Searching associated file %s with %s", file_, grep_prog)
            with subprocess.Popen(
                [
                    grep_prog,
                    *config.commands.search.grep_args,
                    f"-C{context}",
                    query,
                    RelPath(file_).path,
                ],
                stdout=subprocess.PIPE,
            ) as grep:
                if grep.stdout is None:
                    continue
                stdout = grep.stdout
                # extract results
                results = stdout.read().decode().split("\n--\n")
            for match in results:
                if match:
                    matches.append([line.strip() for line in match.split("\n") if line.strip()])

        return matches
