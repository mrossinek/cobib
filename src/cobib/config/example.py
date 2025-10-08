"""An example configuration for coBib.

This module duplicates the default values of `cobib.config.config` in the format of how users would
overwrite any settings. The contents of this module can be extracted using:
```bash
cobib _example_config
```
This dumps the contents to `stdout`. They can be redirected to a desired location like so:
```bash
cobib _example_config > ~/.config/cobib/config.py
```

You can read a description of all available configuration options:
- in the file below (click on `View Source` when viewing this page online)
- at the module-level documentation of `cobib.config`
- in the `cobib-config(5)` manpage (which is rendered online at the previous link)
"""

# Generally, you won't need these, but the default configuration relies on them.
import os
import sys

# To get started you must import coBib's configuration.
from cobib.config import AuthorFormat, JournalFormat, LabelSuffix, TagMarkup, config

# Now, you are all set to apply your own settings.


# COMMANDS

# COMMANDS.ADD

# Whether the automatic file download should be skipped during entry addition.
config.commands.add.skip_download = False

# COMMANDS.DELETE

# Whether to prompt for confirmation before actually deleting an entry.
config.commands.delete.confirm = True
# Whether associated files should be preserved during entry deletion.
config.commands.delete.preserve_files = False

# COMMANDS.EDIT

# The default BibTeX entry type.
config.commands.edit.default_entry_type = "article"
# The editor program. Note that this will respect your _$EDITOR_ environment variable setting,
# falling back to `vim` if that is not set.
config.commands.edit.editor = os.getenv("EDITOR", default="vim")
# Whether associated files should be preserved when renaming entries during editing.
config.commands.edit.preserve_files = False

# COMMANDS.IMPORT

# Whether the download of attachments should be skipped during the import process.
config.commands.import_.skip_download = False

# COMMANDS.LIST

# Whether the filter matching (see also `cobib.commands.list_`) should decode all LaTeX sequences.
config.commands.list_.decode_latex = False
# Whether the filter matching (see also `cobib.commands.list_`) should decode all Unicode
# characters.
config.commands.list_.decode_unicode = False
# The default columns to be displayed during when listing database contents.
config.commands.list_.default_columns = ["label", "title"]
# How many fuzzy errors to allow during the filter matching (see also `cobib.commands.list_`).
# Using this feature requires the optional `regex` dependency to be installed.
config.commands.list_.fuzziness = 0
# Whether the filter matching (see also `cobib.commands.list_`) should be performed
# case-insensitive.
config.commands.list_.ignore_case = False

# COMMANDS.MODIFY

# Whether associated files should be preserved when renaming entries during modifying.
config.commands.modify.preserve_files = False

# COMMANDS.NOTE

# The default filetype to be used for associated notes.
config.commands.note.default_filetype = "txt"

# COMMANDS.OPEN

# The command used to handle opening of `fields` of an entry.
config.commands.open.command = "xdg-open" if sys.platform.lower() == "linux" else "open"
# The names of the entry data fields that are checked for _openable_ URLs.
config.commands.open.fields = ["file", "url"]

# COMMANDS.SEARCH

# The number of lines to provide as a context around search entry matches.
# This is similar to the `-C` option of _grep(1)_.
config.commands.search.context = 1
# Whether searches should decode all LaTeX sequences.
config.commands.search.decode_latex = False
# Whether searches should decode all Unicode characters.
config.commands.search.decode_unicode = False
# How many fuzzy errors to allow during searches.
# Using this feature requires the optional `regex` dependency to be installed.
config.commands.search.fuzziness = 0
# The command used to search the associated _files_ of entries in the database.
# The default tool (_grep(1)_) will not provide search results for attached PDF files, but other
# tools (such as [ripgrep-all](https://github.com/phiresky/ripgrep-all)) will.
config.commands.search.grep = "grep"
# Additional input arguments for the `config.commands.search.grep` command specified as a list of
# strings.
# Note, that GNU's _grep(1)_ understands extended regex patterns even without specifying `-E`.
config.commands.search.grep_args = []
# Whether searches should be performed case-insensitive.
config.commands.search.ignore_case = False
# Whether searches should skip looking through associated _files_ using
# `config.commands.search.grep`.
config.commands.search.skip_files = False
# Whether searches should skip looking through associated _notes_.
# Note, that _notes_ are searched directly with Python rather than through an external system tool.
config.commands.search.skip_notes = False

# COMMANDS.SHOW

# Whether non-ASCII characters should be encoded using LaTeX sequences.
config.commands.show.encode_latex = True


# DATABASE

# The path under which to store already parsed databases. Set this to `None` to disable this
# functionality entirely. See also `cobib.database`.
config.database.cache = "$XDG_CACHE_HOME/cobib/databases/"

# The path to the database YAML file. You can use a `~` to represent your `$HOME` directory. See
# also `cobib.database`.
config.database.file = "$XDG_DATA_HOME/cobib/literature.yaml"

# Whether to enable the _git(1)_ integration, see also `cobib.utils.git`.
config.database.git = False

# DATABASE.FORMAT

# How the `author` field of an entry gets stored.
#
# The `cobib.config.config.AuthorFormat` object is an `Enum` representing the following options:
#   - `YAML`: store the title, first, and last names separately for each author.
#   - `BIBLATEX`: keep the information of all authors as plain text.
config.database.format.author_format = AuthorFormat.YAML

# The default format for the entry `label`s.
# This setting follows the _Python f-string_-like formatting of modifications (see also
# _cobib-modify(1)_). The default simply takes the originally set `label` and passes it through
# [text-unidecode](https://pypi.org/project/text-unidecode/), replacing all Unicode symbols with
# pure ASCII ones. A more useful example is
#     `"{unidecode(author[0].last)}{year}"`
# which takes the surname of the first author
# (assuming `config.database.format.author_format = AuthorFormat.YAML`),
# replacing all Unicode characters with ASCII, and immediately appends the `year`.
config.database.format.label_default = "{unidecode(label)}"

# The suffix format used to disambiguate labels if a conflict would occur.
#
# The value of this setting is a pair:
# The first element is the string used to separate the base label from the enumerator; by default,
# an underscore is used. The second element is one of the `Enum` values of
# `cobib.config.config.LabelSuffix`:
#   - `ALPHA`: a, b, ...
#   - `CAPITAL`: A, B, ...
#   - `NUMERIC`: 1, 2, ...
config.database.format.label_suffix = ("_", LabelSuffix.ALPHA)

# Whether to ignore LaTeX warning during the escaping of special characters. This setting gets
# forwarded to the internally used [pylatexenc](https://pypi.org/project/pylatexenc/) library.
config.database.format.suppress_latex_warnings = True

# Which fields should be left verbatim and, thus, remain unaffected by any special character
# conversions.
config.database.format.verbatim_fields = ["file", "url"]

# DATABASE.STRINGIFY

# The strings used to concatenate the entries in _list_-type fields of an entry when exporting to
# the BibTeX format. The following settings are for the `file`, `tags`, and `url` field, resp.
config.database.stringify.list_separator.file = ", "
config.database.stringify.list_separator.tags = ", "
config.database.stringify.list_separator.url = ", "

# EVENTS

# _cobib-event(7)_ hooks get stored in `config.events` but it should **NOT** be modified directly!
# Instead, the `Event.subscribe` decorator should be used (cf. _cobib-event(7)_).
config.events = {}

# EXPORTERS

# EXPORTERS.BIBTEX

# The form in which to export `journal` names.
config.exporters.bibtex.journal_format = JournalFormat.FULL

# LOGGING

# The default location of the logfile.
config.logging.logfile = "$XDG_STATE_HOME/cobib/cobib.log"
# The default location of the cached version number, based on which `cobib` shows you the
# latest changelog after an update.
# Set this to `None` to disable this functionality entirely.
config.logging.version = "$XDG_CACHE_HOME/cobib/version"

# PARSERS

# PARSERS.BIBTEX

# Whether to ignore non-standard BibTeX entry types.
config.parsers.bibtex.ignore_non_standard_types = False

# PARSERS.YAML

# Whether to use the C-based implementation of the YAML parser.
# This **significantly** improves the performance but may require additional installation steps.
# See the [ruamel.yaml installation instructions](https://yaml.dev/doc/ruamel.yaml/install/) for
# more details.
config.parsers.yaml.use_c_lib_yaml = True

# SHELL

# The path under which to store the history of executed shell commands. Set this to `None` to
# disable this functionality entirely. Using this feature requires the optional `prompt_toolkit`
# dependency to be installed.
config.shell.history = "$XDG_STATE_HOME/cobib/shell_history"

# Whether to enable VI mode (instead of Emacs mode) for `prompt_toolkit`'s line editing.
# Using this feature requires the optional `prompt_toolkit` dependency to be installed.
config.shell.vi_mode = False

# THEME

# Textual's underlying `ColorSystem`.
#
# This setting can either be the name of one of textual's `BUILTIN_THEMES` or an instance of
# `textual.theme.Theme`.
# For a detailed guide, see [textual's documentation](https://textual.textualize.io/guide/design),
# but here is simple example to add an intense splash of color:
#    ```python
#    from textual.theme import BUILTIN_THEMES
#
#    a_splash_of_pink = BUILTIN_THEMES["textual-dark"]
#    a_splash_of_pink.primary = "#ff00ff"
#    config.theme.theme = a_splash_of_pink
#    ```
config.theme.theme = "textual-dark"

# THEME.SEARCH

# The `rich.style.Style` used to highlight the labels of entries that matched a search.
# See [rich's documentation](https://rich.readthedocs.io/en/latest/style.html) for more details.
config.theme.search.label = "blue"
# The `rich.style.Style` used to highlight the actual matches of a search query.
# See [rich's documentation](https://rich.readthedocs.io/en/latest/style.html) for more details.
config.theme.search.query = "red"

# THEME.SYNTAX

# The background color used to display any `rich.syntax.Syntax` elements.
#
# If this is `None`, its default behavior will try to ensure a _transparent_ background. When
# running in the CLI, this implies a value of `"default"`; inside the TUI, textual's _$panel_ color
# variable is used.
# See [textual's documentation](https://textual.textualize.io/guide/design/#base-colors) for more
# details.
config.theme.syntax.background_color = None
# Whether to show line numbers in `rich.syntax.Syntax` elements.
#
# This setting is ignored in side-by-side diff views, where line numbers will **always** show.
config.theme.syntax.line_numbers = True
# The theme used to display any `rich.syntax.Syntax` elements.
#
# If this is `None`, it defaults to `"ansi_dark"` or `"ansi_light"`, in-line with the main textual
# theme. Otherwise, this should be the name of a supported pygments theme.
# See [rich's documentation](https://rich.readthedocs.io/en/latest/syntax.html#theme) for more
# details.
config.theme.syntax.theme = None

# THEME.TAGS

# It is possible to configure special highlighting (or _markup_) for entries with certain _tags_.
# The `TagMarkup` is a pair of an integer, indicating the priority (higher values take precedence),
# and a string describing the `rich.style.Style`.

# The markup for entries with the `high` tag.
config.theme.tags.high = TagMarkup(40, "on bright_red")
# The markup for entries with the `low` tag.
config.theme.tags.low = TagMarkup(20, "bright_yellow")
# The markup for entries with the `medium` tag.
config.theme.tags.medium = TagMarkup(30, "bright_red")
# The markup for entries with the `new` tag.
#
# Note, that this tag does **not** get added automatically.
# But you can do so by subscribing to the _PostAddCommand_ event (see also _cobib-event(7)_):
#    ```python
#    from cobib.config import Event
#
#    @Event.PostAddCommand.subscribe
#    def add_new_tag(cmd: AddCommand) -> None:
#        for entry in cmd.new_entries.values():
#            if "new" not in entry.tags:
#                entry.tags = entry.tags + ["new"]
#    ```
config.theme.tags.new = TagMarkup(10, "bold bright_cyan")
# A dictionary mapping _tag_ names to `TagMarkup` values.
# The _tags_ must be lower case, start with a letter, and only contain letters or the characters
# `.`, `-`, or `_`.
config.theme.tags.user_tags = {}

# TUI

# A list of preset _cobib-filter(7)_ arguments available for quick access in the TUI.
# The first 9 entries of this list can be triggered by pressing the corresponding number in the TUI.
# Pressing `0` resets the filter to the standard list view.
#
# Each entry of this list should be a string describing a _cobib-filter(7)_, for example:
#    ```python
#    config.tui.preset_filters = [
#        "++tags new",   # filters entries with the `new` tag
#        "++year 2023",  # filters entries from the year 2023
#    ]
#    ```
config.tui.preset_filters = []
# The minimum number of lines to keep above and below the cursor in the TUI's list view.
# This is similar to Vim's `scrolloff` option.
config.tui.scroll_offset = 2
# The default folding level of the tree nodes in the TUI's search result view. The two booleans fold
# the node of each matching entry and all its containing search matches, respectively.
config.tui.tree_folding = (True, False)

# UTILS

# The default location for associated files that get downloaded automatically.
config.utils.file_downloader.default_location = "$XDG_DATA_HOME/cobib/"
# A dictionary of _regex patterns_ mapping from article URLs to its corresponding PDF.
#
# Populating this dictionary will improve the success rate of the automatic file download. You can
# find more examples in the [wiki](https://gitlab.com/cobib/cobib/-/wikis/File-Downloader-URL-Maps),
# but here is a simple one:
#    ```python
#    config.utils.file_downloader.url_map[
#        r"(.+)://quantum-journal.org/papers/([^/]+)"
#    ] = r"\1://quantum-journal.org/papers/\2/pdf/"
#    ```
config.utils.file_downloader.url_map = {}

# A list of _journal abbreviations_ as pairs like `("full journal name", "abbrev. name")`.
# The abbreviated version should contain all the necessary punctuation (see also _cobib-export(1)_).
# You can find some examples in the
# [wiki](https://gitlab.com/cobib/cobib/-/wikis/Journal-Abbreviations).
config.utils.journal_abbreviations = []
