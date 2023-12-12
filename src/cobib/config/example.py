"""An example configuration for coBib.

Since version 3.0 coBib is configured through a Python file.
For documentation purposes this example configuration lists all possible settings with their default
values and detailed explanations.

Internally, coBib's configuration is nothing but a (nested) Python dataclass. This means, you can
simply change any setting via an attribute like so:

```python
config.database.git = True
```
"""

# Generally, you won't need these, but the default configuration relies on them.
import os
import sys

# To get started you must import coBib's configuration.
from cobib.config import LabelSuffix, TagMarkup, config

# Now, you are all set to apply your own settings.


# LOGGING
# You can specify the default cache location.
config.logging.cache = "~/.cache/cobib/cache"
# You can specify the default logfile location.
config.logging.logfile = "~/.cache/cobib/cobib.log"
# You can also set the location for the cached version number based on which coBib shows you the
# latest changes. You can set this to `None` to disable this functionality entirely.
config.logging.version = "~/.cache/cobib/version"

# COMMANDS
# These settings affect some command specific behavior.

# You can specify whether the automatic file download should be skipped during entry addition.
config.commands.add.skip_download = False

# You can specify whether you should be prompted for confirmation before deleting an entry.
config.commands.delete.confirm = True
# You can specify whether associated files should be preserved during entry deletion.
config.commands.delete.preserve_files = False

# You can specify the default bibtex entry type.
config.commands.edit.default_entry_type = "article"
# You can specify the editor program. Note, that this default will respect your `$EDITOR`
# environment setting and fall back to `vim` if that variable is not set.
config.commands.edit.editor = os.environ.get("EDITOR", "vim")
# You can specify whether associated files should be preserved when renaming during editing.
config.commands.edit.preserve_files = False

# You can specify whether downloading of attachments inside the imported library should be skipped.
config.commands.import_.skip_download = False

# You can configure the default columns displayed during the list command.
config.commands.list_.default_columns = ["label", "title"]
# You can specify whether filter matching should be performed case-insensitive.
config.commands.list_.ignore_case = False

# You can specify whether associated files should be preserved when renaming during modifying.
config.commands.modify.preserve_files = False

# You can specify a custom command which will be used to `open` files associated with your entries.
config.commands.open.command = "xdg-open" if sys.platform.lower() == "linux" else "open"
# You can specify the names of the data fields which are to be checked for openable URLs.
config.commands.open.fields = ["file", "url"]

# You can specify the default number of context lines to be provided for each search query match.
# This is similar to the `-C` option of `grep`.
config.commands.search.context = 1
# You can specify a custom grep tool which will be used to search through your database and any
# associated files. The default tool (`grep`) will not provide results for attached PDFs but other
# tools such as [ripgrep-all](https://github.com/phiresky/ripgrep-all) will.
config.commands.search.grep = "grep"
# If you want to specify additional arguments for your grep command, you can specify them as a list
# of strings in the following setting. Note, that GNU's grep understands extended regex patterns
# even without specifying `-E`.
config.commands.search.grep_args = []

# You can specify whether searches should be performed case-insensitive.
config.commands.search.ignore_case = False


# DATABASE
# These settings affect the database in general.

# You can specify the path to the database YAML file. You can use a `~` to represent your `$HOME`
# directory.
config.database.file = "~/.local/share/cobib/literature.yaml"

# You can specify the path under which to store already parsed databases. If you want to entirely
# disable caching, set this to `None`.
config.database.cache = "~/.cache/cobib/databases/"

# coBib can integrate with `git` in order to automatically track the history of your database.
# However, by default, this option is disabled. If you want to enable it, simply change the
# following setting to `True` and initialize your database with `cobib init --git`.
# Warning: Before enabling this setting you must ensure that you have set up git properly by setting
# your name and email address.
config.database.git = False

# DATABASE.FORMAT
# You can also specify some aspects about the format of the database.

# You can specify a default label format which will be used for the database entry keys. The format
# of this option follows the f-string like formatting of modifications (see also the documentation
# of the [ModifyCommand](https://cobib.gitlab.io/cobib/cobib/commands/modify.html)). The default
# configuration value passes the originally provided label through
# [text-unidecode](https://pypi.org/project/text-unidecode/) which replaces all Unicode symbols with
# pure ASCII ones. A more useful example is
#     `"{unidecode(author[0].last)}{year}"`
# which takes the surname of the first author, replaces the Unicode characters and then immediately
# appends the publication year.
config.database.format.label_default = "{unidecode(label)}"

# You can specify the suffix format which is used to disambiguate labels if a conflict would occur.
# This option takes a tuple of length 2, where the first entry is the string separating the proposed
# label from the enumerator and the second one is one of the enumerators provided in the
# `config.LabelSuffix` object. The available enumerators are:
#   - ALPHA: a, b, ...
#   - CAPITAL: A, B, ...
#   - NUMERIC: 1, 2, ...
config.database.format.label_suffix = ("_", LabelSuffix.ALPHA)

# You can specify whether latex warnings should not be ignored during the escaping of special
# characters. This is a simple option which gets passed on to the internally used `pylatexenc`
# library.
config.database.format.suppress_latex_warnings = True

# DATABASE.STRINGIFY
# You can customize the functions which convert non-string fields.

# Three fields are currently explicitly stored as lists internally. Upon conversion to the BibTeX
# format, these need to be converted to a basic string. In this process the entries of the list will
# be joined using the separators configured by the following settings.
config.database.stringify.list_separator.file = ", "
config.database.stringify.list_separator.tags = ", "
config.database.stringify.list_separator.url = ", "

# PARSERS
# These settings affect some parser specific behavior.

# You can specify whether the bibtex-parser should ignore non-standard bibtex entry types.
config.parsers.bibtex.ignore_non_standard_types = False

# You can specify that the C-based implementation of the YAML parser (called `LibYAML`) shall be
# used, *significantly* increasing the performance of the parsing. Note, that this requires manual
# installation of the C-based parser:
# https://yaml.readthedocs.io/en/latest/install.html#optional-requirements
config.parsers.yaml.use_c_lib_yaml = True

# THEME

# You can configure the search label and query highlights.
config.theme.search.label = "blue"
config.theme.search.query = "red"

# You can also configure the markup used for the following builtin special tags:
config.theme.tags.new = TagMarkup(10, "bold bright_cyan")
config.theme.tags.high = TagMarkup(40, "on bright_red")
config.theme.tags.medium = TagMarkup(30, "bright_red")
config.theme.tags.low = TagMarkup(20, "bright_yellow")
# None of these tags are added automatically, but you can do this easily with a `PostAddCommand`
# hook like so:
#
#    @Event.PostAddCommand.subscribe
#    def add_new_tag(cmd: AddCommand) -> None:
#        for entry in cmd.new_entries.values():
#            if "new" not in entry.tags:
#                entry.tags = entry.tags + ["new"]
#
# Note, that the `new` tag has a lower weight than all of the builtin priority tags (`high`,
# `medium`, `low`) allowing these to be used to further classify new entries on a reading list.

# You can even specify your own tag names which should be treated with special markup.
# Because the markup names are used in a `rich.Theme`, they must be lower case, start with a letter,
# and only contain letters or the characters `"."`, `"-"`, `"_"`.
config.theme.tags.user_tags = {}

# TUI

# You can configure the minimum number of lines to keep above and below the cursor in the TUI's list
# view. This is similar to Vim's `scrolloff` setting.
config.tui.scroll_offset = 2
# You can configure the default folding level of the tree nodes in the TUI's search result view. The
# first boolean corresponds to the nodes for each matching entry, the second one is for all the
# search matches.
config.tui.tree_folding = (True, False)
# You can provide a list of preset filters. These can be interactively selected in the TUI by
# pressing `p`. To specify these, simply provide a string with the filter arguments, for example:
#
#     config.tui.preset_filters = [
#         "++tags READING",
#         "++year 2023",
#     ]
#
# The first 9 filters can be quickly accessed in the TUI by simply pressing the corresponding
# number. You can also use 0 to reset any applied filter.
config.tui.preset_filters = []

# UTILS

# You can specify the default download location for associated files.
config.utils.file_downloader.default_location = "~/.local/share/cobib"

# You can provide rules to map from a journal's landing page URL to its PDF URL. To do so, you must
# insert an entry into the following dictionary, with a regex-pattern matching the journal's landing
# page URL and a value being the PDF URL. E.g.:
#
#     config.utils.file_downloader.url_map[
#         r"(.+)://aip.scitation.org/doi/([^/]+)"
#     ] = r"\1://aip.scitation.org/doi/pdf/\2"
#
#     config.utils.file_downloader.url_map[
#         r"(.+)://quantum-journal.org/papers/([^/]+)"
#     ] = r"\1://quantum-journal.org/papers/\2/pdf/"
#
# Make sure to use raw Python strings to ensure proper backslash-escaping.
config.utils.file_downloader.url_map = {}

# You can specify a list of journal abbreviations. This list should be formatted as tuples of the
# form: `(full journal name, abbreviation)`. The abbreviation should include any necessary
# punctuation which can be excluded upon export (see also `cobib export --help`).
config.utils.journal_abbreviations = []

# EVENTS
# coBib allows you to register hooks on various events to further customize its behavior to your
# liking. Although these functions will be registered in the following dictionary, we recommend you
# to use the function-decorators as explained below.
config.events = {}
# To subscribe to a certain event do something similar to the following:
#
#     from os import system
#     from pathlib import Path
#     from cobib.config import Event
#
#     @Event.PostInitCommand.subscribe
#     def add_remote(root: Path, file: Path) -> None:
#         system(f"git -C {root} remote add origin https://github.com/user/repo")
#
# Note, that the typing is required for the config validation to pass!
# For more information refer to the
# [online documentation](https://cobib.gitlab.io/cobib/cobib/config/event.html).
