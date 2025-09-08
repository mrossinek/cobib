"""coBib's configuration.

This file contains both, the actual implementation of the `Config` classes, as well as the runtime
`config` object, which gets exposed on the module level as `cobib.config.config`.
Note, that this last link will not point to the correct location in the online documentation due to
the nature of the lower-level import. Instead, at Python runtime this will import
`cobib.config.config.config`.
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
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TextIO

from rich.style import Style
from rich.theme import Theme as RichTheme
from textual.theme import BUILTIN_THEMES
from textual.theme import Theme as TextualTheme
from typing_extensions import override

from cobib.utils.context import get_active_app
from cobib.utils.regex import HAS_OPTIONAL_REGEX
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


@dataclass
class Config(_ConfigBase):
    """The `config` dataclass."""

    commands: CommandConfig = field(default_factory=lambda: CommandConfig())
    """The nested section for the commands settings."""
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
    """The nested section for the database settings."""
    events: dict["Event", list[Callable]] = field(default_factory=dict)  # type: ignore[type-arg]
    """`cobib.config.event` hooks get stored in this dictionary but it should **NOT** be modified
    directly! Instead, the `cobib.config.event.Event.subscribe` decorator should be used (cf.
    `cobib.config.event`)."""
    logging: LoggingConfig = field(default_factory=lambda: LoggingConfig())
    """The nested section for the logging settings."""
    parsers: ParserConfig = field(default_factory=lambda: ParserConfig())
    """The nested section for the parsers settings."""
    shell: ShellConfig = field(default_factory=lambda: ShellConfig())
    """The nested section for the Shell settings."""
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
        self.commands.validate()
        self.database.validate()
        self.logging.validate()
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
        LOGGER.info("Input provided to Config.load: %s", configpath)
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
            # NOTE: I don't quite know why these two lines are not included in coverage because
            # there is a unittest for them and adding a print statement here does show up in the
            # output of the test suite...
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
            spec.loader.exec_module(cfg)  # type: ignore[union-attr]

        try:
            # validate config
            config.validate()
        except RuntimeError as exc:
            LOGGER.error(exc)
            sys.exit(1)


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
    note: NoteCommandConfig = field(default_factory=lambda: NoteCommandConfig())
    """The nested section for settings related to the `note` command."""
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
        self.note.validate()
        self.open.validate()
        self.search.validate()
        self.show.validate()


@dataclass
class AddCommandConfig(_ConfigBase):
    """The `config.commands.add` section."""

    skip_download: bool = False
    """Whether the automatic file download should be skipped during entry addition."""

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
    """Whether to prompt for confirmation before actually deleting an entry."""

    preserve_files: bool = False
    """Whether associated files should be preserved during entry deletion."""

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
    """The default BibTeX entry type."""
    editor: str = os.environ.get("EDITOR", "vim")
    """The editor program. Note that this will respect your `$EDITOR` environment variable setting,
    falling back to `vim` if that is not set."""
    preserve_files: bool = False
    """Whether associated files should be preserved when renaming entries during editing."""

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
    """Whether the download of attachments should be skipped during the import process."""

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

    decode_latex: bool = False
    """Whether the filter matching (see also `cobib.commands.list_`) should decode all LaTeX
    sequences."""
    decode_unicode: bool = False
    """Whether the filter matching (see also `cobib.commands.list_`) should decode all Unicode
    characters."""
    default_columns: list[str] = field(default_factory=lambda: ["label", "title"])
    """The default columns to be displayed during when listing database contents."""
    fuzziness: int = 0
    """How many fuzzy errors to allow during the filter matching (see also `cobib.commands.list_`).
    Using this feature requires the optional `regex` dependency to be installed."""
    ignore_case: bool = False
    """Whether the filter matching (see also `cobib.commands.list_`) should be performed
    case-insensitive."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.LIST configuration section.")
        self._assert(
            isinstance(self.decode_latex, bool),
            "config.commands.list_.decode_latex should be a boolean.",
        )
        self._assert(
            isinstance(self.decode_unicode, bool),
            "config.commands.list_.decode_unicode should be a boolean.",
        )
        self._assert(
            isinstance(self.default_columns, list),
            "config.commands.list_.default_columns should be a list.",
        )
        self._assert(
            isinstance(self.fuzziness, int) and self.fuzziness >= 0,
            "config.commands.list_.fuzziness should be a non-negative integer.",
        )
        # NOTE: we ignore coverage below because the CI has an additional job running the unittests
        # without optional dependencies available.
        if self.fuzziness > 0 and not HAS_OPTIONAL_REGEX:  # pragma: no branch
            LOGGER.warning(  # pragma: no cover
                "Using `config.commands.list_.fuzziness` requires the optional `regex` "
                "dependency to be installed! Falling back to `fuzziness=0`."
            )
            self.fuzziness = 0  # pragma: no cover
        self._assert(
            isinstance(self.ignore_case, bool),
            "config.commands.list_.ignore_case should be a boolean.",
        )


@dataclass
class ModifyCommandConfig(_ConfigBase):
    """The `config.commands.modify` section."""

    preserve_files: bool = False
    """Whether associated files should be preserved when renaming entries during modifying."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.MODIFY configuration section.")
        self._assert(
            isinstance(self.preserve_files, bool),
            "config.commands.modify.preserve_files should be a boolean.",
        )


@dataclass
class NoteCommandConfig(_ConfigBase):
    """The `config.commands.note` section."""

    default_filetype: str = "txt"
    """The default filetype to be used for associated notes."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.NOTE configuration section.")
        self._assert(
            isinstance(self.default_filetype, str),
            "config.commands.note.default_filetype should be a string.",
        )


@dataclass
class OpenCommandConfig(_ConfigBase):
    """The `config.commands.open` section."""

    command: str = "xdg-open" if sys.platform.lower() == "linux" else "open"
    """The command used to handle opening of `fields` of an entry."""
    fields: list[str] = field(default_factory=lambda: ["file", "url"])
    """The names of the entry data fields that are checked for *openable* URLs."""

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
    """The number of lines to provide as a context around search entry matches. This is similar to
    the `-C` option of `grep(1)`."""
    decode_latex: bool = False
    """Whether searches should decode all LaTeX sequences."""
    decode_unicode: bool = False
    """Whether searches should decode all Unicode characters."""
    fuzziness: int = 0
    """How many fuzzy errors to allow during searches. Using this feature requires the optional
    `regex` dependency to be installed."""
    grep: str = "grep"
    """The command used to search the associated files of entries in the database. The default tool
    (`grep(1)`) will not provide search results for attached PDF files, but other tools (such as
    [ripgrep-all](https://github.com/phiresky/ripgrep-all)) will."""
    grep_args: list[str] = field(default_factory=list)
    """Additional input arguments for the `config.commands.search.grep` command specified as a list
    of strings. Note, that GNU's `grep(1)` understands extended regex patterns even without
    specifying `-E`."""
    ignore_case: bool = False
    """Whether searches should be performed case-insensitive."""
    skip_files: bool = False
    """Whether searches should skip looking through associated *files* using
    `config.commands.search.grep`."""
    skip_notes: bool = False
    """Whether searches should skip looking through associated *notes*. Note, that *notes* are
    searched directly with Python rather than through an external system tool."""

    @property
    def highlights(self) -> SearchHighlightConfig:  # pragma: no cover
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
            isinstance(self.decode_latex, bool),
            "config.commands.search.decode_latex should be a boolean.",
        )
        self._assert(
            isinstance(self.decode_unicode, bool),
            "config.commands.search.decode_unicode should be a boolean.",
        )
        self._assert(
            isinstance(self.fuzziness, int) and self.fuzziness >= 0,
            "config.commands.search.fuzziness should be a non-negative integer.",
        )
        if self.fuzziness > 0 and not HAS_OPTIONAL_REGEX:
            # NOTE: we are ignoring coverage below, because the codebase is checked separately
            # without optional dependencies being present.
            LOGGER.warning(  # pragma: no cover
                "Using `config.commands.search.fuzziness` requires the optional `regex` "
                "dependency to be installed! Falling back to `fuzziness=0`."
            )
            self.fuzziness = 0  # pragma: no cover
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
        self._assert(
            isinstance(self.skip_files, bool),
            "config.commands.search.skip_files should be a boolean.",
        )
        self._assert(
            isinstance(self.skip_notes, bool),
            "config.commands.search.skip_notes should be a boolean.",
        )


@dataclass
class ShowCommandConfig(_ConfigBase):
    """The `config.commands.show` section."""

    encode_latex: bool = True
    """Whether non-ASCII characters should be encoded using LaTeX sequences."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the COMMANDS.SHOW configuration section.")
        self._assert(
            isinstance(self.encode_latex, bool),
            "config.commands.show.encode_latex should be a boolean.",
        )


@dataclass
class DatabaseConfig(_ConfigBase):
    """The `config.database` section."""

    cache: str | Path | None = "~/.cache/cobib/databases/"
    """The path under which to store already parsed databases. Set this to `None` to disable this
    functionality entirely. See also `cobib.database`."""
    file: str | Path = "~/.local/share/cobib/literature.yaml"
    """The path to the database YAML file. You can use a `~` to represent your `$HOME` directory.
    See also `cobib.database`."""
    format: DatabaseFormatConfig = field(default_factory=lambda: DatabaseFormatConfig())
    """The nested section for database formatting settings."""
    git: bool = False
    """Whether to enable the `git(1)` integration, see also `cobib.utils.git`."""
    stringify: EntryStringifyConfig = field(default_factory=lambda: EntryStringifyConfig())
    """The nested section for database string-formatting settings."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the DATABASE configuration section.")
        self._assert(
            self.cache is None or isinstance(self.cache, (str, Path)),
            "config.database.cache should be a string, Path, or `None`.",
        )
        self._assert(
            isinstance(self.file, (str, Path)), "config.database.file should be a string or Path."
        )
        self.format.validate()
        self._assert(isinstance(self.git, bool), "config.database.git should be a boolean.")
        self.stringify.validate()


class AuthorFormat(Enum):
    """Storage formats for the `author` information."""

    YAML = auto()
    """Stores the list of authors as a YAML list, separating out the first and last names as well as
    name pre- and suffixes."""
    BIBLATEX = auto()
    """Stores the author in the same form as it would be encoded inside of BibLaTeX."""


class LabelSuffix(Enum):
    """Suffixes to disambiguate `cobib.database.Entry` labels."""

    ALPHA = lambda count: chr(96 + count)
    """Enumerates with lowercase roman letters: `a-z`."""
    CAPITAL = lambda count: chr(64 + count)
    """Enumerates with uppercase roman letters: `A-Z`."""

    NUMERIC = lambda count: str(count)
    """Enumerates with arabic numbers: `1, 2, ...`."""

    @staticmethod
    def reverse(type_: LabelSuffix, suffix: str) -> int:
        """Reverses a label suffix enumerator from a suffix to its integer value.

        Args:
            type_: the `LabelSuffix` enumerator.
            suffix: the suffix to reverse.

        Returns:
            The integer value of the reversed suffix.

        Raises:
            ValueError: if a non-numeric suffix is longer than 1 character.
            ValueError: if an alphabetic suffix did not fall within the alphabet.
            ValueError: if an invalid suffix of some other form is provided.
        """
        # TODO: once Python 3.10 becomes the default, change this to a match statement

        if type_ == LabelSuffix.NUMERIC:
            return int(suffix)

        if len(suffix) > 1:
            raise ValueError("A non-numeric suffix may not be longer than a single character.")

        if type_ in {LabelSuffix.ALPHA, LabelSuffix.CAPITAL}:
            # we can convert both of these cases in the same way by using base 36 for `int()`
            ret = int(suffix, 36) - 9
            if ret < 0:
                raise ValueError(
                    f"'{suffix}' is not a valid alphabetic suffix because its ANSI value falls "
                    "outside of the alphabetic range, yielding a negative value."
                )
            return ret

        raise ValueError(f"'{suffix}' is not a valid suffix.")

    @staticmethod
    def suffix_type(suffix: str) -> LabelSuffix | None:
        """Determines the enumerator type for a given suffix.

        Args:
            suffix: the suffix whose enumerator type to determine.

        Returns:
            An optional enumerator type. If the suffix was invalid, `None` will be returned.
        """
        if not suffix.isascii():
            # if the input contains a non-ASCII character, it cannot be a label suffix
            return None

        try:
            # test if the suffix is numeric by attempting to convert it to a base-10 integer
            _ = int(suffix)
        except ValueError:
            # first ensure that we have only alphabetic characters left
            if not suffix.isalpha():
                # this is important, because for example "hello123" will pass `islower()` because
                # all of the cased characters are indeed lower-cased
                return None

            if suffix.islower():
                return LabelSuffix.ALPHA
            if suffix.isupper():
                return LabelSuffix.CAPITAL
        else:
            return LabelSuffix.NUMERIC

        # the provided suffix did not match any of the builtin enumerators
        return None

    @staticmethod
    def trim_label(label: str, separator: str, type_: LabelSuffix) -> tuple[str, int]:
        """Trims the provided label based on the separator and suffix type.

        Args:
            label: the label whose suffix to trim.
            separator: the separator character between the actual label and the suffix.
            type_: the `LabelSuffix` enumerator.

        Returns:
            The pair of the trimmed label and numeric value of its original suffix.
        """
        # initialize the counter of the suffix
        suffix_value = 0

        # try split the suffix from the label using the provided separator
        if separator:
            *pieces, suffix = label.split(separator)
        else:
            # no character is used for separation, we simply fall back to using the last one
            suffix = label[-1]
            pieces = [label[:-1]]

        if pieces:
            # piece together the left-over raw label without its suffix
            raw_label = separator.join(pieces)
            # determine the suffix type of this label
            suffix_type = LabelSuffix.suffix_type(suffix)

            if suffix_type is not None and suffix_type != type_:
                # if it does not match the expected suffix type, ignore it
                LOGGER.info(
                    f"The suffix type encountered on '{label}' does not match the configured one. "
                    "Assuming that this is intentional and therefore ignoring this as a suffix."
                )
                raw_label = label
            else:
                try:
                    # try to obtain the suffix value by reversing it
                    suffix_value = LabelSuffix.reverse(type_, suffix)
                except ValueError:
                    # if this fails, reset the raw label and assume that this was not an actual
                    # disambiguation suffix
                    raw_label = label
        else:
            # the original split did not yield any pieces so the `suffix` is the actual `raw_label`
            raw_label = suffix

        return (raw_label, suffix_value)


@dataclass
class DatabaseFormatConfig(_ConfigBase):
    """The `config.database.format` section."""

    author_format: AuthorFormat = AuthorFormat.YAML
    """How the `author` field of an entry gets stored. See `AuthorFormat` for more details."""
    label_default: str = "{unidecode(label)}"
    """The default format for the entry `label`s.

    This setting follows the _Python f-string_-like formatting of modifications (see also
    `cobib.commands.modify`). The default simply takes the originally set `label` and passes it
    through [text-unidecode](https://pypi.org/project/text-unidecode/), replacing all Unicode
    symbols with pure ASCII ones. A more useful example is

        `"{unidecode(author[0].last)}{year}"`

    which takes the surname of the first author (assuming `config.database.format.author_format =
    AuthorFormat.YAML`), replacing all Unicode characters with ASCII, and immediately appends the
    `year`.
    """
    label_suffix: tuple[str, LabelSuffix] = field(default_factory=lambda: ("_", LabelSuffix.ALPHA))
    """The suffix format used to disambiguate labels if a conflict would occur.

    The value of this setting is a pair:
    The first element is the string used to separate the base label from the enumerator; by default,
    an underscore is used.
    The second element is one of the `Enum` values of `cobib.config.config.LabelSuffix`:
        - `ALPHA`: a, b, ...
        - `CAPITAL`: A, B, ...
        - `NUMERIC`: 1, 2, ...
    """
    suppress_latex_warnings: bool = True
    """Whether to ignore LaTeX warning during the escaping of special characters. This setting gets
    forwarded to the internally used [pylatexenc](https://pypi.org/project/pylatexenc/) library."""
    verbatim_fields: list[str] = field(default_factory=lambda: ["file", "url"])
    """Which fields should be left verbatim and, thus, remain unaffected by any special character
    conversions."""

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
class LoggingConfig(_ConfigBase):
    """The `config.logging` section."""

    cache: str | Path = "~/.cache/cobib/cache"
    """The default location of the cache."""
    logfile: str | Path = "~/.cache/cobib/cobib.log"
    """The default location of the logfile."""
    version: str | None = "~/.cache/cobib/version"
    """The default location of the cached version number, based on which `cobib` shows you the
    latest changelog after an update. Set this to `None` to disable this functionality entirely."""

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
class BibtexParserConfig(_ConfigBase):
    """The `config.parsers.bibtex` section."""

    ignore_non_standard_types: bool = False
    """Whether to ignore non-standard BibTeX entry types."""

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
    """Whether to use the C-based implementation of the YAML parser.

    This **significantly** improves the performance but may require additional installation steps.
    See the [ruamel.yaml installation instructions](https://yaml.dev/doc/ruamel.yaml/install/) for
    more details."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the PARSERS.YAML configuration section.")
        self._assert(
            isinstance(self.use_c_lib_yaml, bool),
            "config.parsers.yaml.use_c_lib_yaml should be a boolean.",
        )


@dataclass
class ShellConfig(_ConfigBase):
    """The `config.shell` section."""

    history: str | Path | None = "~/.cache/cobib/shell_history"
    """The path under which to store the history of executed shell commands (i.e. the argument to
    `prompt_toolkit.history.FileHistory`). Set this to `None` to disable this functionality entirely
    (i.e. to use `prompt_toolkit.history.InMemoryHistory`). See also [this explanation][1].

    Using this feature requires the optional `prompt_toolkit` dependency to be installed.

    [1]: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#history
    """

    vi_mode: bool = False
    """Whether to enable VI mode (instead of Emacs mode) for `prompt_toolkit`'s line editing.
    Using this feature requires the optional `prompt_toolkit` dependency to be installed."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the SHELL configuration section.")
        self._assert(
            self.history is None or isinstance(self.history, (str, Path)),
            "config.shell.history should be a string, Path, or `None`.",
        )
        self._assert(isinstance(self.vi_mode, bool), "config.shell.vi_mode should be a boolean.")


@dataclass
class ThemeConfig(_ConfigBase):
    """The `config.theme` section."""

    search: SearchHighlightConfig = field(default_factory=lambda: SearchHighlightConfig())
    """The nested section for theme settings related to the `search` command."""
    syntax: SyntaxConfig = field(default_factory=lambda: SyntaxConfig())
    """The nested section for theme settings related to `rich.Syntax` displays."""
    tags: TagsThemeConfig = field(default_factory=lambda: TagsThemeConfig())
    """The nested section for the markup of special tags."""
    theme: str | TextualTheme = "textual-dark"
    """Textual's underlying `ColorSystem`.

    This setting can either be the name of one of textual's `BUILTIN_THEMES` or an instance of
    `textual.theme.Theme`.
    For a detailed guide, see [textual's documentation](https://textual.textualize.io/guide/design),
    but here is simple example to add an intense splash of color:
       ```python
       from textual.theme import BUILTIN_THEMES

       a_splash_of_pink = BUILTIN_THEMES["textual-dark"]
       a_splash_of_pink.primary = "#ff00ff"
       config.theme.theme = a_splash_of_pink
       ```
    """

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the THEME configuration section.")
        self.search.validate()
        self.syntax.validate()
        self.tags.validate()
        self._assert(
            isinstance(self.theme, (str, TextualTheme)),
            "config.theme.theme must be the name of or an actual textual.theme.Theme",
        )

    def build(self) -> RichTheme:
        """Returns the built `rich.Theme` from the configured styles."""
        theme: dict[str, str | Style] = {}
        theme.update(self.search.styles)
        theme.update(self.tags.styles)
        return RichTheme(theme)

    @property
    def textual_theme(self) -> TextualTheme:
        """Returns the `textual.theme.Theme`."""
        return self.theme if isinstance(self.theme, TextualTheme) else BUILTIN_THEMES[self.theme]

    @property
    def css_variables(self) -> dict[str, str]:
        """The actual CSS color variables generated from the active theme of `ThemeConfig.theme`.

        Returns:
            A dictionary mapping from color names to values. See [textual's
            documentation](https://textual.textualize.io/guide/design) for more details.
        """
        return self.textual_theme.to_color_system().generate()


@dataclass
class SearchHighlightConfig(_ConfigBase):
    """The `config.theme.search` section."""

    label: str | Style = "blue"
    """The `rich.style.Style` used to highlight the labels of entries that matched a search.

    See [rich's documentation](https://rich.readthedocs.io/en/latest/style.html) for more
    details."""
    query: str | Style = "red"
    """The `rich.style.Style` used to highlight the actual matches of a search query.

    See [rich's documentation](https://rich.readthedocs.io/en/latest/style.html) for more
    details."""

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
class SyntaxConfig(_ConfigBase):
    """The `config.theme.syntax` section.

    These attributes configure the default values used for displaying `rich.Syntax` elements.
    """

    background_color: str | None = None
    """The background color used to display any `rich.syntax.Syntax` elements.

    If this is `None`, its default behavior will try to ensure a *transparent* background. When
    running in the CLI, this implies a value of `"default"`; inside the TUI, textual's `$panel`
    color variable is used. See [textual's
    documentation](https://textual.textualize.io/guide/design/#base-colors) for more details.

    This attribute should be accessed via the `SyntaxConfig.get_background_color` method.
    """

    line_numbers: bool = True
    """Whether to show line numbers in `rich.syntax.Syntax` elements.

    .. note::
        This setting is ignored in side-by-side diff views, where line numbers will **always** show.
    """

    theme: str | None = None
    """The theme used to display any `rich.syntax.Syntax` elements.

    If this is `None`, it defaults to `"ansi_dark"` or `"ansi_light"`, in-line with the main textual
    theme. Otherwise, this should be the name of a supported pygments theme. See [rich's
    documentation](https://rich.readthedocs.io/en/latest/syntax.html#theme) for more details.

    This attribute should be accessed via the `SyntaxConfig.get_theme` method.
    """

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the THEME.SYNTAX configuration section.")
        self._assert(
            self.background_color is None or isinstance(self.background_color, str),
            "config.theme.syntax.background_color should either be `None` or a string.",
        )
        self._assert(
            isinstance(self.line_numbers, bool),
            "config.theme.syntax.line_numbers should be a boolean.",
        )
        self._assert(
            self.theme is None or isinstance(self.theme, str),
            "config.theme.syntax.theme should either be `None` or a string.",
        )

    def get_theme(self) -> str:
        """Returns the `SyntaxConfig.theme` value."""
        if self.theme is not None:
            return self.theme

        return "ansi_dark" if config.theme.textual_theme.dark else "ansi_light"

    def get_background_color(self) -> str:
        """Returns the `SyntaxConfig.background_color` value."""
        if self.background_color is not None:
            return self.background_color

        if get_active_app() is None:
            return "default"

        return config.theme.css_variables["panel"]


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

    high: TagMarkup = TagMarkup(40, "on bright_red")
    """The markup for entries with the `high` tag."""
    low: TagMarkup = TagMarkup(20, "bright_yellow")
    """The markup for entries with the `low` tag."""
    medium: TagMarkup = TagMarkup(30, "bright_red")
    """The markup for entries with the `medium` tag."""
    new: TagMarkup = TagMarkup(10, "bold bright_cyan")
    """The markup for entries with the `new` tag.

    Note, that this tag does **not** get added automatically.
    But you can do so by subscribing to the `cobib.config.event.Event.PostAddCommand` event (see
    also `cobib.config.event`):
    ```python
    from cobib.config import Event

    @Event.PostAddCommand.subscribe
    def add_new_tag(cmd: AddCommand) -> None:
        for entry in cmd.new_entries.values():
            if "new" not in entry.tags:
                entry.tags = entry.tags + ["new"]
    ```
    """
    user_tags: dict[str, TagMarkup] = field(default_factory=dict)
    """A dictionary mapping *tag* names to `TagMarkup` values.

    The *tags* must be lower case, start with a letter, and only contain letters or the characters
    `.`, `-`, or `_`.
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
            isinstance(self.high, TagMarkup), "config.theme.tags.high should be a TagMarkup tuple."
        )
        self._assert(
            isinstance(self.low, TagMarkup), "config.theme.tags.low should be a TagMarkup tuple."
        )
        self._assert(
            isinstance(self.medium, TagMarkup),
            "config.theme.tags.medium should be a TagMarkup tuple.",
        )
        self._assert(
            isinstance(self.new, TagMarkup), "config.theme.tags.new should be a TagMarkup tuple."
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
class TUIConfig(_ConfigBase):
    """The `config.tui` section."""

    preset_filters: list[str] = field(default_factory=list)
    """A list of preset *filter* (see also `cobib.database.entry`) arguments available for quick
    access in the TUI.

    The first 9 entries of this list can be triggered by pressing the corresponding number in the
    TUI. Pressing `0` resets the filter to the standard list view.

    Each entry of this list should be a string describing a *filter*, for example:
       ```python
       config.tui.preset_filters = [
           "++tags new",   # filters entries with the `new` tag
           "++year 2023",  # filters entries from the year 2023
       ]
       ```
    """
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
    scroll_offset: int = 2
    """The minimum number of lines to keep above and below the cursor in the TUI's list view.
    This is similar to Vim's `scrolloff` option."""
    tree_folding: tuple[bool, bool] = (True, False)
    """The default folding level of the tree nodes in the TUI's search result view. The two booleans
    fold the node of each matching entry and all its containing search matches, respectively."""

    @override
    def validate(self) -> None:
        LOGGER.debug("Validating the TUI configuration section.")
        self._assert(
            isinstance(self.preset_filters, list),
            "config.tui.preset_filters should be a list.",
        )
        for preset in self.preset_filters:
            self._assert(
                isinstance(preset, str),
                "config.tui.preset_filters should be a list of strings.",
            )
        self._assert(
            isinstance(self.scroll_offset, int),
            "config.tui.scroll_offset should be an integer.",
        )
        self._assert(
            isinstance(self.tree_folding, tuple) and len(self.tree_folding) == 2,  # noqa: PLR2004
            "config.tui.tree_folding should be a tuple of length 2.",
        )
        self._assert(
            isinstance(self.tree_folding[0], bool),
            "The first element in config.tui.tree_folding should be a boolean.",
        )
        self._assert(
            isinstance(self.tree_folding[1], bool),
            "The second element in config.tui.tree_folding should be a boolean.",
        )


@dataclass
class UtilsConfig(_ConfigBase):
    """The `config.utils` section."""

    file_downloader: FileDownloaderConfig = field(default_factory=lambda: FileDownloaderConfig())
    """The nested section for the `cobib.utils.FileDownloader` utils settings."""
    journal_abbreviations: list[tuple[str, str]] = field(default_factory=list)
    """A list of *journal abbreviations* as pairs like `("full journal name", "abbrev. name")`.
    The abbreviated version should contain all the necessary punctuation (see also
    `cobib.commands.export`).

    You can find some examples in the
    [wiki](https://gitlab.com/cobib/cobib/-/wikis/Journal-Abbreviations).
    """

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
class FileDownloaderConfig(_ConfigBase):
    """The `config.utils.file_downloader` section."""

    default_location: str = "~/.local/share/cobib/"
    """The default location for associated files that get downloaded automatically."""
    url_map: dict[str, str] = field(default_factory=dict)
    """A dictionary of *regex patterns* mapping from article URLs to its corresponding PDF.

    Populating this dictionary will improve the success rate of the automatic file download.
    You can find more examples in the
    [wiki](https://gitlab.com/cobib/cobib/-/wikis/File-Downloader-URL-Maps),
    but here is a simple one:
       ```python
       config.utils.file_downloader.url_map[
           r"(.+)://quantum-journal.org/papers/([^/]+)"
       ] = r"\1://quantum-journal.org/papers/\2/pdf/"
       ```
    """

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


config = Config()
"""This is the runtime configuration object. It is exposed on the module level via:
```python
from cobib.config import config
```
"""
config.defaults()
