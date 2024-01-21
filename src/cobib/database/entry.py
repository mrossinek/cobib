"""coBib's Entry class."""

from __future__ import annotations

import logging
import re
import subprocess
from typing import TYPE_CHECKING, Any, List, Optional, cast

from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexencode import UnicodeToLatexEncoder

from cobib.config import AuthorFormat, config
from cobib.utils.rel_path import RelPath

from .author import Author

if TYPE_CHECKING:
    import cobib.parsers

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


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

    _unicode_to_latex_encoder: UnicodeToLatexEncoder | None = None
    """The singleton `UnicodeToLatexEncoder` used by all instances of this class."""

    @classmethod
    def _get_unicode_to_latex_encoder(cls) -> UnicodeToLatexEncoder:
        """Returns the `_unicode_to_latex_encoder` singleton and constructs it if necessary."""
        if cls._unicode_to_latex_encoder is None:
            cls._unicode_to_latex_encoder = UnicodeToLatexEncoder(
                non_ascii_only=True,
                replacement_latex_protection="braces-all",
                unknown_char_policy="keep",
                unknown_char_warning=not config.database.format.suppress_latex_warnings
                or LOGGER.isEnabledFor(logging.DEBUG),
            )

        return cls._unicode_to_latex_encoder

    _latex_to_text_decoder: LatexNodes2Text | None = None
    """The singleton `LatexNodes2Text` used by all instances of this class."""

    @classmethod
    def _get_latex_to_text_decoder(cls) -> LatexNodes2Text:
        """Returns the `_latex_to_text_decoder` singleton and constructs it if necessary."""
        if cls._latex_to_text_decoder is None:
            cls._latex_to_text_decoder = LatexNodes2Text(keep_braced_groups=True)

        return cls._latex_to_text_decoder

    def __init__(self, label: str, data: dict[str, Any]) -> None:
        """Initializes a new Entry.

        Args:
            label: the label associated with this entry in the `Database`.
            data: the actual bibliographic data stored as a dictionary mapping free-form field names
                (`str`) to any other data. Some fields are exposed as properties of this class for
                convenience.
        """
        LOGGER.debug("Initializing entry: %s", label)

        self._label: str = str(label)

        self.data: dict[str, Any] = {}
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

    def merge(self, other: Entry, *, ours: bool = False) -> None:
        """Merges the current entry with the other one.

        Args:
            other: the other entry.
            ours: a boolean indicating which data takes precedence. `True` indicates that `self`
                takes precedence over `other` which means that `other.update(self)` will be run
                (`self` overwrites values in `other`). `False` (the default) indicates the opposite.
        """
        if ours:
            other_data = other.data.copy()
            other_data.update(self.data)
            self.data = other_data.copy()
        else:
            self.data.update(other.data)

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

    def markup_label(self) -> str:
        """Returns the label of this entry with the rich markup based on special tags."""
        markup_label = self.label

        markup_tags: dict[str, int] = {}
        for tag in self.tags:
            if tag in config.theme.tags.names:
                markup_tags[f"tag.{tag}"] = config.theme.tags.weights[tag]

        for tag, _ in sorted(markup_tags.items(), key=lambda item: item[1], reverse=True):
            markup_label = f"[{tag}]{markup_label}[/{tag}]"

        return markup_label

    @property
    def author(self) -> str:
        """The author of this entry formatted as a single string.

        Internally, the author(s) may be stored as one or more strings or `cobib.database.Author`
        instances. In this case, they will be joined into a single string of unified formatting
        before returned by this method.

        Returns:
            The string-formatted author(s) of this entry.

        References:
            - https://www.bibtex.com/f/author-field/
        """
        authors = self.data.get("author", "")

        if isinstance(authors, str):
            return authors

        if isinstance(authors, list):
            author_string = ""
            for author in authors:
                if author_string:
                    author_string += " and "
                author_string += str(author)
            return author_string

        return ""

    @author.setter
    def author(self, authors: str | list[str] | list[dict[str, str]] | list[Author]) -> None:
        """Sets the author of this entry.

        The input is processed in two steps.
        1. any encountered LaTeX commands are decoded into Unicode.
        2. each author is parsed by `cobib.database.Author.parse`.

        Args:
            authors: can be a single string, list of strings, list of `cobib.database.Author`
                objects, or a list of dictionaries mapping strings to strings which are treated as
                the key-value pairs to reconstruct a `cobib.database.Author` named tuple instance.

        References:
            - https://www.bibtex.com/f/author-field/
        """
        if not isinstance(authors, list):
            authors = authors.split(" and ")

        dec = self._get_latex_to_text_decoder()

        parsed_authors: list[str | Author] = []
        for author in authors:
            if isinstance(author, Author):
                parsed_authors.append(author)
                continue
            if isinstance(author, dict):
                parsed_authors.append(Author(**author))
                continue

            # we explicitly convert any latex instructions to Unicode
            author = cast(str, dec.latex_to_text(author))  # noqa: PLW2901
            LOGGER.debug("Converted the author to Unicode: '%s'", author)

            parsed_author = Author.parse(author)
            if config.database.format.author_format == AuthorFormat.YAML and not isinstance(
                parsed_author, str
            ):
                LOGGER.info(
                    "Parsed the author '%s' of entry '%s' from a string to the more detailed "
                    "information. You can consider storing it as such directly.",
                    author,
                    self.label,
                    extra={"entry": self.label, "field": "author"},
                )
            parsed_authors.append(parsed_author)

        self.data["author"] = parsed_authors

    @property
    def tags(self) -> list[str]:
        """The tags of this entry."""
        return cast(List[str], self.data.get("tags", []))

    @tags.setter
    def tags(self, tags: str | list[str]) -> None:
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
    def file(self) -> list[str]:
        """The associated files of this entry.

        The setter of this property will convert the strings to paths relative to the user's home
        directory. Internally, this field will always be stored as a list.
        """
        return cast(List[str], self.data.get("file", []))

    @file.setter
    def file(self, file: str | list[str]) -> None:
        """Sets the associated files of this entry.

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
    def url(self) -> list[str]:
        """The associated URL(s) of this entry."""
        return cast(List[str], self.data.get("url", []))

    @url.setter
    def url(self, url: str | list[str]) -> None:
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
    def month(self) -> str | None:
        """Returns the month."""
        return cast(Optional[str], self.data.get("month", None))

    @month.setter
    def month(self, month: int | str) -> None:
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

    def stringify(self, *, encode_latex: bool = True, markup: bool = False) -> dict[str, str]:
        """Returns an identical entry to self but with all fields converted to strings.

        Args:
            encode_latex: whether to encode non-ASCII characters using LaTeX sequences. If this is
                `True`, a `pylatexenc.latexencode.UnicodeToLatexEncoder` will be used to replace
                Unicode characters with LaTeX commands.
            markup: whether or not to add markup based on the configured special tags.

        Returns:
            The data of this `Entry` as pure string fields.
        """
        if encode_latex:
            enc = self._get_unicode_to_latex_encoder()
        data = {}
        data["label"] = self.markup_label() if markup else self.label
        for field, value in self.data.items():
            if hasattr(self, field):
                value = getattr(self, field)  # noqa: PLW2901
            if field == "author":
                data[field] = str(value)
            elif isinstance(value, list) and hasattr(
                config.database.stringify.list_separator, field
            ):
                data[field] = getattr(config.database.stringify.list_separator, field).join(value)
            else:
                data[field] = str(value)
            if encode_latex:
                data[field] = enc.unicode_to_latex(data[field])
        return data

    def formatted(self) -> Entry:
        """Formats the entry in a clean and reproducible manner.

        This includes the following:

        1. escaping of special characters; these should be escaped to ensure proper rendering in
           LaTeX documents. This function leverages the existing implementation of the `pylatexenc`
           module to do said conversion. The only fields exempted from the conversion are those

        2. handles the `cobib.config.config.DatabaseFormatConfig.author_format` setting and outputs
           the `author` field in the corresponding format.

        Returns:
            A new `Entry` instance with all fields properly formatted.
        """
        enc = self._get_unicode_to_latex_encoder()
        formatted_entry = Entry(self.label, {})
        for key, value in self.data.items():
            if key in config.database.format.verbatim_fields:
                # do NOT these fields and keep any special characters
                formatted_entry.data[key] = value
                continue

            if key == "author":
                if config.database.format.author_format == AuthorFormat.BIBLATEX:
                    formatted_entry.data[key] = enc.unicode_to_latex(self.author)
                elif config.database.format.author_format == AuthorFormat.YAML:
                    formatted_entry.data[key] = value
                continue

            if isinstance(value, str):
                formatted_entry.data[key] = enc.unicode_to_latex(value)
            else:
                formatted_entry.data[key] = value

        return formatted_entry

    def save(self, parser: cobib.parsers.base_parser.Parser | None = None) -> str:
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
        formatted_entry = self.formatted()
        if parser is None:
            from cobib.parsers.yaml import YAMLParser

            parser = YAMLParser()
        return parser.dump(formatted_entry) or ""  # `dump` may return `None`

    def matches(
        self, filter_: dict[tuple[str, bool], list[str]], or_: bool, ignore_case: bool = False
    ) -> bool:
        """Check whether this entry matches the supplied filter.

        coBib provides an extensive filtering implementation. The filter is specified in the form
        of a dictionary whose keys consist of pairs of `(str, bool)` entries where the string
        indicates the field to match against and the boolean whether a positive (`true`) or negative
        (`false`) match is required. The values of the dictionary must be a `list[str]`. This means
        that field types are always compared on a string-basis (this is a limitation of the targeted
        command-line interface). However, as of v3.2.0 these strings are interpreted as regex
        patterns providing the most power within this framework.

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
            ignore_case: if True, the matching will be case-*in*sensitive.

        Returns:
            Boolean indicating whether this entry matches the filter.
        """
        LOGGER.debug("Checking whether entry %s matches.", self.label)
        re_flags = re.IGNORECASE if ignore_case else 0
        match_list = []
        stringified_data = self.stringify(encode_latex=False)
        for key, values in filter_.items():
            if key[0] not in stringified_data:
                match_list.append(not key[1])
                continue
            for val in values:
                if re.search(rf"{val}", stringified_data[key[0]], flags=re_flags):
                    match_list.append(key[1])
                else:
                    match_list.append(not key[1])
        if or_:
            return any(m for m in match_list)
        return all(m for m in match_list)

    def search(
        self,
        query: list[str],
        context: int = 1,
        ignore_case: bool = False,
        skip_files: bool = False,
    ) -> list[list[str]]:
        """Search entry contents for the query strings.

        The entry will *always* be converted to a searchable string using the
        `cobib.parsers.BibtexParser.dump` method. This text will then be search for each item in
        `query` and will interpret these as regex patterns.
        If a `file` is associated with this entry, the search will try its best to recursively query
        its contents, too. However, the success of this depends highly on the configured search
        tool, `cobib.config.config.SearchCommandConfig.grep`.

        Args:
            query: the list of regex patterns to search for.
            context: the number of context lines to provide for each match. This behaves similarly
                to the *Context Line Control* available for the UNIX `grep` command (`--context`).
            ignore_case: if True, the search will be case-*in*sensitive.
            skip_files: if True, associated files will *not* be searched.

        Returns:
            A list of lists containing the context for each match associated with this entry.
        """
        LOGGER.debug("Searching entry %s.", self.label)
        matches: list[list[str]] = []

        from cobib.parsers.bibtex import BibtexParser

        bibtex = BibtexParser(encode_latex=False).dump(self).split("\n")
        re_flags = re.IGNORECASE if ignore_case else 0
        for query_str in query:
            re_compiled = re.compile(rf"{query_str}", flags=re_flags)
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

            if skip_files:
                LOGGER.debug("Skipping the search in associated files of %s", self.label)
                continue

            for file_ in self.file:
                grep_prog = config.commands.search.grep
                path = RelPath(file_).path
                if not path.exists():
                    LOGGER.warning(
                        "The associated file %s of entry %s does not exist!", file_, self.label
                    )
                    continue

                LOGGER.debug("Searching associated file %s with %s", file_, grep_prog)
                with subprocess.Popen(
                    [
                        grep_prog,
                        *config.commands.search.grep_args,
                        f"-C{context}",
                        query_str,
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
