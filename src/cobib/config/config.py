"""coBib's configuration.

This file contains both, the actual implementation of the `Config` classes, as well as the runtime
`config` object, which gets exposed on the module level as `cobib.config.config`.
Note, that this last link will not point to the correct location in the online documentation due to
the nature of the lower-level import.
"""
# ruff: noqa: E731, RUF009

from __future__ import annotations

import importlib.util
import io
import logging
import os
import sys
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import MISSING, dataclass, field, fields
from enum import Enum, EnumMeta, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, TextIO

from rich.style import Style
from rich.theme import Theme
from typing_extensions import override

from cobib.utils.rel_path import RelPath

if TYPE_CHECKING:
    import rich

    from .event import Event

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


@dataclass
class _ConfigBase:
    """Base class for configuration section dataclasses."""

    @staticmethod
    def _assert(expression: bool, error: str) -> None:
        """Asserts the expression is True.

        Args:
            expression: the expression to assert.
            error: the message of the `RuntimeError` upon assertion failure.

        Raises:
            RuntimeError with the specified error string.
        """
        if not expression:
            raise RuntimeError(error)

    @abstractmethod
    def validate(self) -> None:
        """Validates the configuration at runtime.

        Raises:
            RuntimeError when an invalid setting is encountered.
        """

    def defaults(self) -> None:
        """Resets the configuration to the default settings."""
        for name, field_ in self.__dataclass_fields__.items():
            if field_.default != MISSING:
                setattr(self, name, field_.default)
            else:
                setattr(self, name, field_.default_factory())  # type: ignore[misc]


class TagMarkup(NamedTuple):
    """A tuple for representing the weight and style of a tag."""

    weight: int
    """The weight of the tag. This integer is used to determine the markup priority of the tag.
    Higher integer values indicate a higher priority."""
    style: str | rich.style.Style
    """The style of the tag. This can be a `rich.style.Style` or a string which can be interpreted
    by `rich.style.Style.parse`."""


@dataclass
class TagsThemeConfig(_ConfigBase):
    """The markup configuration for special tags.

    The tag names configured via this setting will be marked up via a `rich.Theme`. This allows you
    to easily customize a visual differentiation of your entries based on simple properties.

    The style and weight of the builtin special tags can be configured directly or you can add fully
    custom special tags via the `user_tags` field.
    """

    new: TagMarkup = TagMarkup(10, "bold bright_cyan")
    """The markup of the `new` tag. By default, coBib does *not* add this automatically, but you can
    do this easily with a `PostAddCommand` hook like so:

    ```python
    @Event.PostAddCommand.subscribe
    def add_new_tag(cmd: AddCommand) -> None:
        for entry in cmd.new_entries.values():
            if "new" not in entry.tags:
                entry.tags = entry.tags + ["new"]
    ```

    .. note::
       The `new` tag has a lower weight than all of the builtin priority tags (`high`, `medium`,
       `low`) allowing these to be used to further classify new entries on a reading list.
    """
    high: TagMarkup = TagMarkup(40, "on bright_red")
    """The markup of the `high` priority tag."""
    medium: TagMarkup = TagMarkup(30, "bright_red")
    """The markup of the `medium` priority tag."""
    low: TagMarkup = TagMarkup(20, "bright_yellow")
    """The markup of the `low` priority tag."""
    user_tags: dict[str, TagMarkup] = field(default_factory=dict)
    """A dictionary to add weight and markup definitions for arbitrary tags. The keys of the
    dictionary will be compared as is to the tags of an `cobib.database.entry.Entry`.

    .. note::
       Because the markup names are used in a `rich.Theme`, they must be lower case, start with a
       letter, and only contain letters or the characters `"."`, `"-"`, `"_"`. See also
       [here](https://rich.readthedocs.io/en/stable/style.html#style-themes).
    """

    @property
    def names(self) -> set[str]:
        """Returns the set of all special tag names."""
        return {f.name for f in fields(self)} - {"user_tags"} | set(self.user_tags.keys())

    @property
    def styles(self) -> dict[str, str | Style]:
        """Returns the combined dictionary of all special tag styles."""
        styles: dict[str, str | Style] = {}
        for field_ in fields(self):
            tag_markup = getattr(self, field_.name)
            if isinstance(tag_markup, TagMarkup):
                styles[f"tag.{field_.name}"] = tag_markup.style

        for name, weighted_style in self.user_tags.items():
            styles[f"tag.{name}"] = weighted_style.style

        return styles

    @property
    def weights(self) -> dict[str, int]:
        """Returns the combined dictionary of all special tag weights."""
        weights: dict[str, int] = {}
        for field_ in fields(self):
            tag_markup = getattr(self, field_.name)
            if isinstance(tag_markup, TagMarkup):
                weights[field_.name] = tag_markup.weight

        for name, weighted_style in self.user_tags.items():
            weights[name] = weighted_style.weight

        return weights

    @override
    def validate(self) -> None:
        self._assert(
            isinstance(self.new, TagMarkup), "config.theme.tags.new should be a TagMarkup tuple."
        )
        self._assert(
            isinstance(self.high, TagMarkup), "config.theme.tags.high should be a TagMarkup tuple."
        )
        self._assert(
            isinstance(self.medium, TagMarkup),
            "config.theme.tags.medium should be a TagMarkup tuple.",
        )
        self._assert(
            isinstance(self.low, TagMarkup), "config.theme.tags.low should be a TagMarkup tuple."
        )
        self._assert(
            isinstance(self.user_tags, dict),
            "config.theme.tags.user_tags should be a dict.",
        )
        for name, tag_markup in self.user_tags.items():
            self._assert(
                isinstance(tag_markup, TagMarkup),
                f"The '{name}' entry in config.theme.tags.user_tags should be a TagMarkup tuple.",
            )


@dataclass
class SearchHighlightConfig(_ConfigBase):
    """The `config.theme.search` section."""

    label: str | Style = "blue"
    """Specifies the color with which to highlight the labels of search results."""
    query: str | Style = "red"
    """Specifies the color with which to highlight the query matches of a search."""

    @property
    def styles(self) -> dict[str, str | Style]:
        """Returns the `rich.Theme`-compatible styles dictionary of the configured highlights."""
        return {
            "search.label": self.label,
            "search.query": self.query,
        }

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the THEME.SEARCH configuration section.")
        self._assert(isinstance(self.label, str), "config.theme.search.label should be a string.")
        self._assert(isinstance(self.query, str), "config.theme.search.query should be a string.")


@dataclass
class ThemeConfig(_ConfigBase):
    """The `config.theme` section."""

    search: SearchHighlightConfig = field(default_factory=lambda: SearchHighlightConfig())
    """The nested section for theme settings related to the `search` command."""
    tags: TagsThemeConfig = field(default_factory=lambda: TagsThemeConfig())
    """The nested section for the markup of special tags."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the THEME configuration section.")
        self.search.validate()
        self.tags.validate()

    def build(self) -> Theme:
        """Returns the built `rich.Theme` from the configured styles."""
        theme: dict[str, str | Style] = {}
        theme.update(self.search.styles)
        theme.update(self.tags.styles)
        return Theme(theme)


@dataclass
class LoggingConfig(_ConfigBase):
    """The `config.logging` section."""

    cache: str | Path = "~/.cache/cobib/cache"
    """Specifies the default cache location."""
    logfile: str | Path = "~/.cache/cobib/cobib.log"
    """Specifies the default logfile location."""
    version: str | None = "~/.cache/cobib/version"
    """Specifies the location for the cached version number based on which coBib shows the latest
    changes. Set this to `None` to disable this functionality entirely."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the LOGGING configuration section.")
        self._assert(
            isinstance(self.cache, (str, Path)), "config.logging.cache should be a string."
        )
        self._assert(
            isinstance(self.logfile, (str, Path)), "config.logging.logfile should be a string."
        )
        self._assert(
            self.version is None or isinstance(self.version, str),
            "config.logging.version should be a string or `None`.",
        )


@dataclass
class AddCommandConfig(_ConfigBase):
    """The `config.commands.add` section."""

    skip_download: bool = False
    """Specifies whether to skip the attempt of downloading PDF files of added entries."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.ADD configuration section.")
        self._assert(
            isinstance(self.skip_download, bool),
            "config.commands.add.skip_download should be a boolean.",
        )


@dataclass
class DeleteCommandConfig(_ConfigBase):
    """The `config.commands.delete` section."""

    confirm: bool = True
    """Whether or not to confirm before deleting an entry."""

    preserve_files: bool = False
    """Specifies whether associated files should be preserved when deleting an entry."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.DELETE configuration section.")
        self._assert(
            isinstance(self.confirm, bool),
            "config.commands.delete.confirm should be a boolean.",
        )
        self._assert(
            isinstance(self.preserve_files, bool),
            "config.commands.delete.preserve_files should be a boolean.",
        )


@dataclass
class EditCommandConfig(_ConfigBase):
    """The `config.commands.edit` section."""

    default_entry_type: str = "article"
    """Specifies the default bibtex entry type."""
    editor: str = os.environ.get("EDITOR", "vim")
    """Specifies the editor program. Note, that this default will respect your `$EDITOR`
    environment setting and fall back to `vim` if that variable is not set."""
    preserve_files: bool = False
    """Specifies whether associated files should be preserved when renaming an entry during
    editing."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.EDIT configuration section.")
        self._assert(
            isinstance(self.default_entry_type, str),
            "config.commands.edit.default_entry_type should be a string.",
        )
        self._assert(
            isinstance(self.editor, str),
            "config.commands.edit.editor should be a string.",
        )
        self._assert(
            isinstance(self.preserve_files, bool),
            "config.commands.edit.preserve_files should be a boolean.",
        )


@dataclass
class ImportCommandConfig(_ConfigBase):
    """The `config.commands.import` section."""

    skip_download: bool = False
    """Specifies whether to skip the attempt of downloading PDF files of imported entries."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.IMPORT configuration section.")
        self._assert(
            isinstance(self.skip_download, bool),
            "config.commands.import.skip_download should be a boolean.",
        )


@dataclass
class ListCommandConfig(_ConfigBase):
    """The `config.commands.list_` section."""

    default_columns: list[str] = field(default_factory=lambda: ["label", "title"])
    """Specifies the default columns shown during the `list` command."""
    ignore_case: bool = False
    """Specifies whether filter matching should be performed case-insensitive."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.LIST configuration section.")
        self._assert(
            isinstance(self.default_columns, list),
            "config.commands.list_.default_columns should be a list.",
        )
        self._assert(
            isinstance(self.ignore_case, bool),
            "config.commands.list_.ignore_case should be a boolean.",
        )


@dataclass
class ModifyCommandConfig(_ConfigBase):
    """The `config.commands.modify` section."""

    preserve_files: bool = False
    """Specifies whether associated files should be preserved when renaming an entry during
    modifying."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.MODIFY configuration section.")
        self._assert(
            isinstance(self.preserve_files, bool),
            "config.commands.modify.preserve_files should be a boolean.",
        )


@dataclass
class OpenCommandConfig(_ConfigBase):
    """The `config.commands.open` section."""

    command: str = "xdg-open" if sys.platform.lower() == "linux" else "open"
    """Specifies the command used for opening files associated with your entries."""
    fields: list[str] = field(default_factory=lambda: ["file", "url"])
    """Specifies the entry fields which are to be checked for openable URLs."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.OPEN configuration section.")
        self._assert(
            isinstance(self.command, str),
            "config.commands.open.command should be a string.",
        )
        self._assert(
            isinstance(self.fields, list),
            "config.commands.open.fields should be a list.",
        )


@dataclass
class SearchCommandConfig(_ConfigBase):
    """The `config.commands.search` section."""

    context: int = 1
    """Specifies the default number of context line to provide for each search query match. This is
    similar to the `-C` option of `grep`."""
    grep: str = "grep"
    """Specifies the grep tool used for searching through your database and associated files. The
    default tool (`grep`) will not provide results for attached PDFs but other tools such as
    [ripgrep-all](https://github.com/phiresky/ripgrep-all) will."""
    grep_args: list[str] = field(default_factory=list)
    """Specifies additional arguments for your grep command. Note, that GNU's grep understands
    extended regex patterns even without specifying `-E`."""
    ignore_case: bool = False
    """Specifies whether searches should be performed case-insensitive."""

    @property
    def highlights(self) -> SearchHighlightConfig:
        """**DEPRECATED** Use `config.theme.search` instead!

        The nested section for highlights used when displaying search results.
        """
        LOGGER.log(
            45,
            "The config.commands.search.highlights setting is DEPRECATED! Please use the new "
            "config.theme.search setting instead.",
        )
        return config.theme.search

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.SEARCH configuration section.")
        self._assert(
            isinstance(self.context, int) and self.context >= 0,
            "config.commands.search.context should be a non-negative integer.",
        )
        self._assert(
            isinstance(self.grep, str),
            "config.commands.search.grep should be a string.",
        )
        self._assert(
            isinstance(self.grep_args, list),
            "config.commands.search.grep_args should be a list.",
        )
        self._assert(
            isinstance(self.ignore_case, bool),
            "config.commands.search.ignore_case should be a boolean.",
        )


@dataclass
class ShowCommandConfig(_ConfigBase):
    """The `config.commands.show` section."""

    encode_latex: bool = True
    """Specifies whether non-ASCII characters should be encoded using LaTeX sequences."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.SHOW configuration section.")
        self._assert(
            isinstance(self.encode_latex, bool),
            "config.commands.show.encode_latex should be a boolean.",
        )


@dataclass
class CommandConfig(_ConfigBase):
    """The `config.commands` section."""

    add: AddCommandConfig = field(default_factory=lambda: AddCommandConfig())
    """The nested section for settings related to the `add` command."""
    delete: DeleteCommandConfig = field(default_factory=lambda: DeleteCommandConfig())
    """The nested section for settings related to the `delete` command."""
    edit: EditCommandConfig = field(default_factory=lambda: EditCommandConfig())
    """The nested section for settings related to the `edit` command."""
    import_: ImportCommandConfig = field(default_factory=lambda: ImportCommandConfig())
    """The nested section for settings related to the `import` command. Note the trailing underscore
    of its name, since this attribute would otherwise clash with the builtin `import` keyword."""
    list_: ListCommandConfig = field(default_factory=lambda: ListCommandConfig())
    """The nested section for settings related to the `list` command. Note the trailing underscore
    of its name, since this attribute would otherwise clash with the builtin `list` keyword."""
    modify: ModifyCommandConfig = field(default_factory=lambda: ModifyCommandConfig())
    """The nested section for settings related to the `modify` command."""
    open: OpenCommandConfig = field(default_factory=lambda: OpenCommandConfig())
    """The nested section for settings related to the `open` command."""
    search: SearchCommandConfig = field(default_factory=lambda: SearchCommandConfig())
    """The nested section for settings related to the `search` command."""
    show: ShowCommandConfig = field(default_factory=lambda: ShowCommandConfig())
    """The nested section for settings related to the `show` command."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS configuration section.")
        self.add.validate()
        self.delete.validate()
        self.edit.validate()
        self.import_.validate()
        self.list_.validate()
        self.modify.validate()
        self.open.validate()
        self.search.validate()
        self.show.validate()


class _DeprecateOnAccess(EnumMeta):
    """A metaclass to add deprecation warnings to deprecated Enum values upon access."""

    @override
    def __getattribute__(cls, name: str) -> Any:
        if name == "CAPTIAL":
            LOGGER.log(
                45,
                "The LabelSuffix.CAPTIAL value is deprecated! Please switch to the correctly "
                "spelled LabelSuffix.CAPITAL instead.",
            )
        return super().__getattribute__(name)

    @override
    def __getitem__(cls, name: str) -> Any:
        if name == "CAPTIAL":
            LOGGER.log(
                45,
                "The LabelSuffix.CAPTIAL value is deprecated! Please switch to the correctly "
                "spelled LabelSuffix.CAPITAL instead.",
            )
        return super().__getitem__(name)


class LabelSuffix(Enum, metaclass=_DeprecateOnAccess):
    """Suffixes to disambiguate `cobib.database.Entry` labels."""

    ALPHA = lambda count: chr(96 + count)
    """Enumerates with lowercase roman letters: `a-z`."""
    CAPITAL = lambda count: chr(64 + count)
    """Enumerates with uppercase roman letters: `A-Z`."""

    NUMERIC = lambda count: str(count)
    """Enumerates with arabic numbers: `1, 2, ...`."""
    CAPTIAL = lambda count: chr(64 + count)
    """**Deprecated!** This is a deprecated mistyped name of `LabelSuffix.CAPITAL`."""


class AuthorFormat(Enum):
    """Storage formats for the `author` information."""

    YAML = auto()
    """Stores the list of authors as a YAML list, separating out the first and last names as well as
    name pre- and suffixes."""
    BIBLATEX = auto()
    """Stores the author in the same form as it would be encoded inside of BibLaTeX."""


@dataclass
class DatabaseFormatConfig(_ConfigBase):
    """The `config.database.format` section."""

    author_format: AuthorFormat = AuthorFormat.YAML
    """Specifies the format to use for the `author` information. See also `AuthorFormat` for more
    details."""
    label_default: str = "{unidecode(label)}"
    """Specifies a default label format which will be used for database entry keys. The format of
    this option follows the f-string like formatting of modifications (see also the documentation
    of the `cobib.commands.modify.ModifyCommand`). The default configuration value passes the
    originally provided label through [text-unidecode](https://pypi.org/project/text-unidecode/)
    which replaces all Unicode symbols with pure ASCII ones. A more useful example is
    `"{unidecode(author[0].last)}{year}"` which takes the surname of the first author, replaces the
    Unicode characters and then immediately appends the publication year."""
    label_suffix: tuple[str, LabelSuffix] = field(default_factory=lambda: ("_", LabelSuffix.ALPHA))
    """Specifies the suffix format which is used to disambiguate labels if a conflict would occur.
    This option takes a tuple of length 2, where the first entry is the string separating the
    proposed label from the enumerator and the second one is one of the enumerators provided by the
    `LabelSuffix` object. The available enumerators are:
        - ALPHA: a, b, ...
        - CAPITAL: A, B, ...
        - NUMERIC: 1, 2, ...
    """
    suppress_latex_warnings: bool = True
    """Specifies whether latex warnings should not be ignored during the escaping of special
    characters. This is a simple option which gets passed on to the internally used `pylatexenc`
    library."""
    verbatim_fields: list[str] = field(default_factory=lambda: ["file", "url"])
    """Specifies the fields which will be left verbatim and, thus, remain unaffected from any
    special character conversions (e.g. LaTeX encoding)."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the DATABASE.FORMAT configuration section.")
        self._assert(
            isinstance(self.author_format, AuthorFormat),
            "config.database.format.author_format should be an AuthorFormat value.",
        )
        self._assert(
            isinstance(self.label_default, str),
            "config.database.format.label_default should be a string.",
        )
        self._assert(
            isinstance(self.label_suffix, tuple) and len(self.label_suffix) == 2,  # noqa: PLR2004
            "config.database.format.label_suffix should be a tuple of length 2.",
        )
        self._assert(
            isinstance(self.label_suffix[0], str),
            "The first entry of config.database.format.label_suffix should be a string.",
        )
        self._assert(
            callable(self.label_suffix[1]),
            "The first entry of config.database.format.label_suffix should be a function.",
        )
        self._assert(
            isinstance(self.suppress_latex_warnings, bool),
            "config.database.format.suppress_latex_warnings should be a boolean.",
        )
        self._assert(
            isinstance(self.verbatim_fields, list),
            "config.database.format.verbatim_fields should be a list.",
        )


@dataclass
class EntryListSeparatorConfig(_ConfigBase):
    """The `config.database.stringify.list_separator` section.

    These settings configure how list-based `cobib.database.Entry` fields are transformed into
    strings when converting to the BibTeX format. Each of these fields will be joined by the
    respective values.
    """

    file: str = ", "
    """Specifies the string used to join the list of files into a single string representation."""
    tags: str = ", "
    """Specifies the string used to join the list of tags into a single string representation."""
    url: str = ", "
    """Specifies the string used to join the list of URLs into a single string representation."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the DATABASE.STRINGIFY.LIST_SEPARATOR configuration section.")
        self._assert(
            isinstance(self.file, str),
            "config.database.stringify.list_separator.file should be a string.",
        )
        self._assert(
            isinstance(self.tags, str),
            "config.database.stringify.list_separator.tags should be a string.",
        )
        self._assert(
            isinstance(self.url, str),
            "config.database.stringify.list_separator.url should be a string.",
        )


@dataclass
class EntryStringifyConfig(_ConfigBase):
    """The `config.database.stringify` section."""

    list_separator: EntryListSeparatorConfig = field(
        default_factory=lambda: EntryListSeparatorConfig()
    )
    """The nested section for list separator values."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the DATABASE.STRINGIFY configuration section.")
        self.list_separator.validate()


@dataclass
class DatabaseConfig(_ConfigBase):
    """The `config.database` section."""

    file: str | Path = "~/.local/share/cobib/literature.yaml"
    """Specifies the path to the database YAML file. You can use `~` to represent your `$HOME`
    directory."""
    cache: str | Path | None = "~/.cache/cobib/databases/"
    """Specifies the folder in which already parsed databases should be stored. Set this to `None`
    if you want to disable caching entirely."""
    format: DatabaseFormatConfig = field(default_factory=lambda: DatabaseFormatConfig())
    """The nested section for database formatting settings."""
    git: bool = False
    """coBib can integrate with `git` in order to automatically track the history of the database.
    However, by default, this option is disabled. In order to make use of this, enable this setting
    and initialize your database with `cobib init --git`.

    .. warning::
       Before enabling this setting you must ensure that you have set up git properly by setting
       your name and email address."""
    stringify: EntryStringifyConfig = field(default_factory=lambda: EntryStringifyConfig())
    """The nested section for database string-formatting settings."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the DATABASE configuration section.")
        self._assert(isinstance(self.file, str), "config.database.file should be a string.")
        self._assert(
            self.cache is None or isinstance(self.cache, str),
            "config.database.cache should be a string or `None`.",
        )
        self._assert(isinstance(self.git, bool), "config.database.git should be a boolean.")
        self.format.validate()
        self.stringify.validate()


@dataclass
class BibtexParserConfig(_ConfigBase):
    """The `config.parsers.bibtex` section."""

    ignore_non_standard_types: bool = False
    """Specifies whether the BibTeX-parser should ignore non-standard BibTeX entry types."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the PARSERS.BIBTEX configuration section.")
        self._assert(
            isinstance(self.ignore_non_standard_types, bool),
            "config.parsers.bibtex.ignore_non_standard_types should be a boolean.",
        )


@dataclass
class YAMLParserConfig(_ConfigBase):
    """The `config.parsers.yaml` section."""

    use_c_lib_yaml: bool = True
    """Specifies whether the C-based implementation of the YAML parser (called `LibYAML`) shall be
    used, *significantly* increasing the performance of the parsing.

    .. note::
       This requires manual installation of the C-based parser:
       https://yaml.readthedocs.io/en/latest/install.html#optional-requirements
    """

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the PARSERS.YAML configuration section.")
        self._assert(
            isinstance(self.use_c_lib_yaml, bool),
            "config.parsers.yaml.use_c_lib_yaml should be a boolean.",
        )


@dataclass
class ParserConfig(_ConfigBase):
    """The `config.parsers` section."""

    bibtex: BibtexParserConfig = field(default_factory=lambda: BibtexParserConfig())
    """The nested section for the BibTeX parser settings."""
    yaml: YAMLParserConfig = field(default_factory=lambda: YAMLParserConfig())
    """The nested section for the YAML parser settings."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the PARSERS configuration section.")
        self.bibtex.validate()
        self.yaml.validate()


@dataclass
class TUIConfig(_ConfigBase):
    """The `config.tui` section."""

    scroll_offset: int = 2
    """The minimum number of lines to keep above and below the cursor in the
    `cobib.ui.tui.components.ListView`. This is similar to Vim's `scrolloff` setting."""
    tree_folding: tuple[bool, bool] = (True, False)
    """The default folding level of the tree nodes in the `cobib.ui.tui.components.SearchView`. When
    `True`, the node will be initialized to be folded (or collapsed), when `False`, it will be
    expanded. The first boolean corresponds to the nodes for each matching entry, the second one is
    for all the search matches."""
    preset_filters: list[str] = field(default_factory=list)
    """Permits providing a list of preset filters. These can be interactively selected in the TUI by
    pressing `p`. To specify these, simply provide a string with the filter arguments, for example:

    ```python
    config.tui.preset_filters = [
        "++tags READING",
        "++year 2023",
    ]
    ```

    The first 9 filters can be quickly accessed in the TUI by simply pressing the corresponding
    number. You can also use 0 to reset any applied filter."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the TUI configuration section.")
        self._assert(
            isinstance(self.scroll_offset, int),
            "config.tui.scroll_offset should be an integer.",
        )
        self._assert(
            isinstance(self.preset_filters, list),
            "config.tui.preset_filters should be a list.",
        )
        for preset in self.preset_filters:
            self._assert(
                isinstance(preset, str),
                "config.tui.preset_filters should be a list of strings.",
            )


@dataclass
class FileDownloaderConfig(_ConfigBase):
    """The `config.utils.file_downloader` section."""

    default_location: str = "~/.local/share/cobib"
    """Specifies the default download location for associated files."""
    url_map: dict[str, str] = field(default_factory=dict)
    """Permits providing rules to map from a journal's landing page URL to its PDF URL. To do so,
    insert an entry into this dictionary, with a regex-pattern matching the journal's landing page
    URL and a value being the PDF URL. E.g.:

    ```python
    config.utils.file_downloader.url_map[
        r"(.+)://aip.scitation.org/doi/([^/]+)"
    ] = r"\1://aip.scitation.org/doi/pdf/\2"

    config.utils.file_downloader.url_map[
        r"(.+)://quantum-journal.org/papers/([^/]+)"
    ] = r"\1://quantum-journal.org/papers/\2/pdf/"
    ```

    Make sure to use raw Python strings to ensure proper backslash-escaping.

    You can find some examples on
    [this wiki page](https://gitlab.com/cobib/cobib/-/wikis/File-Downloader-URL-Maps)."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the UTILS.FILE_DOWNLOADER configuration section.")
        self._assert(
            isinstance(self.default_location, str),
            "config.utils.file_downloader.default_location should be a string.",
        )
        self._assert(
            isinstance(self.url_map, dict),
            "config.utils.file_downloader.url_map should be a dict.",
        )
        for pattern, repl in self.url_map.items():
            self._assert(
                isinstance(pattern, str) and isinstance(repl, str),
                "config.utils.file_downloader.url_map should be a dict[str, str].",
            )


@dataclass
class UtilsConfig(_ConfigBase):
    """The `config.utils` section."""

    file_downloader: FileDownloaderConfig = field(default_factory=lambda: FileDownloaderConfig())
    """The nested section for the `cobib.utils.FileDownloader` utils settings."""
    journal_abbreviations: list[tuple[str, str]] = field(default_factory=list)
    """Permits providing a list of journal abbreviations. This list should be formatted as tuples of
    the form: `(full journal name, abbreviation)`. The abbreviation should include any necessary
    punctuation which can be excluded upon export (see also `cobib export --help`).

    You can find some examples on
    [this wiki page](https://gitlab.com/cobib/cobib/-/wikis/Journal-Abbreviations)."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the UTILS configuration section.")
        self.file_downloader.validate()
        self._assert(
            isinstance(self.journal_abbreviations, list),
            "config.utils.journal_abbreviations should be a list.",
        )
        for abbrev in self.journal_abbreviations:
            self._assert(
                isinstance(abbrev, tuple),
                "config.utils.journal_abbreviations should be a list of tuples.",
            )


@dataclass
class Config(_ConfigBase):
    """The `config` dataclass."""

    logging: LoggingConfig = field(default_factory=lambda: LoggingConfig())
    """The nested section for the logging settings."""
    commands: CommandConfig = field(default_factory=lambda: CommandConfig())
    """The nested section for the commands settings."""
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
    """The nested section for the database settings."""
    events: dict["Event", list[Callable]] = field(default_factory=dict)  # type: ignore[type-arg]
    """It is possible to register hooks on various events. Although this can be done manually using
    this dictionary, it is preferred to use the function-decorators like so:
    To subscribe to a certain event do something similar to the following:

    ```python
    from os import system
    from cobib.config import Event
    from cobib.commands import InitCommand

    @Event.PostInitCommand.subscribe
    def add_remote(cmd: InitCommand) -> None:
        system(f"git -C {cmd.root} remote add origin https://github.com/user/repo")
    ```

    Note, that the typing is required for the config validation to pass!
    For more information refer to the `cobib.config.Event` documentation.
    """
    parsers: ParserConfig = field(default_factory=lambda: ParserConfig())
    """The nested section for the parsers settings."""
    theme: ThemeConfig = field(default_factory=lambda: ThemeConfig())
    """The nested section for the theme settings."""
    tui: TUIConfig = field(default_factory=lambda: TUIConfig())
    """The nested section for the TUI settings."""
    utils: UtilsConfig = field(default_factory=lambda: UtilsConfig())
    """The nested section for the utils settings."""

    XDG_CONFIG_FILE: str | Path = field(
        default="~/.config/cobib/config.py", init=False, repr=False, compare=False
    )
    """The XDG-based standard configuration location."""

    @override
    def validate(self) -> None:
        LOGGER.info("Validating the runtime configuration.")
        self.logging.validate()
        self.commands.validate()
        self.database.validate()
        self.parsers.validate()
        self.theme.validate()
        self.tui.validate()
        self.utils.validate()

        LOGGER.debug("Validating the EVENTS configuration section.")
        self._assert(isinstance(self.events, dict), "config.events should be a dict.")
        for event in self.events:
            self._assert(
                event.validate(),
                f"config.events.{event} did not pass its validation check.",
            )

    @staticmethod
    def load(configpath: str | Path | TextIO | io.TextIOWrapper | None = None) -> None:
        """Loads another configuration object at runtime.

        WARNING: The new Python-like configuration allows essentially arbitrary Python code so it is
        the user's responsibility to treat this with care!

        Args:
            configpath: the path to the configuration.
        """
        LOGGER.info(configpath)
        if configpath is not None:
            if isinstance(configpath, (TextIO, io.TextIOWrapper)):
                configpath.close()
                configpath = configpath.name
        elif "COBIB_CONFIG" in os.environ:
            configpath_env = os.environ["COBIB_CONFIG"]
            if configpath_env.lower() in ("", "0", "f", "false", "nil", "none"):
                LOGGER.info(
                    "Skipping configuration loading because negative COBIB_CONFIG environment "
                    "variable was detected."
                )
                return
            configpath = RelPath(configpath_env).path
        elif Config.XDG_CONFIG_FILE and RelPath(Config.XDG_CONFIG_FILE).exists():
            configpath = RelPath(Config.XDG_CONFIG_FILE).path
        else:  # pragma: no cover
            return  # pragma: no cover
        LOGGER.info("Loading configuration from default location: %s", configpath)

        spec = importlib.util.spec_from_file_location("config", configpath)
        if spec is None:
            LOGGER.error(
                "The config at %s could not be interpreted as a Python module.", configpath
            )
            sys.exit(1)
        else:
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)  # type: ignore

        try:
            # validate config
            config.validate()
        except RuntimeError as exc:
            LOGGER.error(exc)
            sys.exit(1)


config = Config()
"""This is the runtime configuration object. It is exposed on the module level via:
```python
from cobib.config import config
```
"""
config.defaults()
