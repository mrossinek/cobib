cobib-config(5) -- the configuration specification for cobib(1)
===============================================================

## SYNOPSIS

`cobib` `--config`=_PATH_ ...<br>
`COBIB_CONFIG`=_PATH_ `cobib` ...<br>
`$HOME/.config/cobib/config.py`

## DESCRIPTION

The [SYNOPSIS][] section above outlines the different means of configuring _cobib(1)_ in order of precedence.
In the first two cases, _PATH_ must point to a Python file which includes the actual configuration settings.
The last case indicates the default location which is checked for a user configuration file.
If none of those are set, the internal defaults will be used.

Being a Python module, the configuration file should import the default configuration like so:

```python
from cobib.config import config
```

The `config` object contains all of the attributes outlined in the [OPTIONS][] section below.
Those can be overwritten to ones desire.

Check the [EXAMPLES][] section to see how to populate a file with all default settings.

It is possible to fully disable the loading of a configuration file by setting _$COBIB_CONFIG_ to one of the following values:
`""`, `0`, `"f"`, `"false"`, `"nil"`, `"none"`.

## OPTIONS

We separate the options into subsections based on what they configure.

### COMMANDS

#### COMMANDS.ADD

  * _config.commands.add.skip_download_ = `False`:
    Whether the automatic file download should be skipped during entry addition.

#### COMMANDS.DELETE

  * _config.commands.delete.confirm_ = `True`:
    Whether to prompt for confirmation before actually deleting an entry.

  * _config.commands.delete.preserve_files_ = `False`:
    Whether associated files should be preserved during entry deletion.

#### COMMANDS.EDIT

  * _config.commands.edit.default_entry_type_ = `"article"`:
    The default BibTeX entry type.

  * _config.commands.edit.editor_ = `os.environ.get("EDITOR", "vim")`:
    The editor program.
    Note that this will respect your _$EDITOR_ environment variable setting, falling back to `vim` if that is not set.

  * _config.commands.edit.preserve_files_ = `False`:
    Whether associated files should be preserved when renaming entries during editing.

#### COMMANDS.IMPORT

  * _config.commands.import\_.skip_download_ = `False`:
    Whether the download of attachments should be skipped during the import process.

#### COMMANDS.LIST

  * _config.commands.list\_.decode_latex_ = `False`:
    Whether the _cobib-filter(7)_ matching should decode all LaTeX sequences.

  * _config.commands.list\_.decode_unicode_ = `False`:
    Whether the _cobib-filter(7)_ matching should decode all Unicode characters.

  * _config.commands.list\_.default_columns_ = `["label", "title"]`:
    The default columns to be displayed during when listing database contents.

  * _config.commands.list\_.fuzziness_ = `0`:
    How many fuzzy errors to allow during the _cobib-filter(7)_ matching.
    Using this feature requires the optional `regex` dependency to be installed.

  * _config.commands.list\_.ignore_case_ = `False`:
    Whether the _cobib-filter(7)_ matching should be performed case-insensitive.

#### COMMANDS.MODIFY

  * _config.commands.modify.preserve_files_ = `False`:
    Whether associated files should be preserved when renaming entries during modifying.

#### COMMANDS.NOTE

  * _config.commands.note.default_filetype_ = `"txt"`:
    The default filetype to be used for associated notes.

#### COMMANDS.OPEN

  * _config.commands.open.command_ = `"xdg-open" if sys.platform.lower() == "linux" else "open"`:
    The command used to handle opening of `fields` of an entry.

  * _config.commands.open.fields_ = `["file", "url"]`:
    The names of the entry data fields that are checked for _openable_ URLs.

#### COMMANDS.SEARCH

  * _config.commands.search.context_ = `1`:
    The number of lines to provide as a context around search entry matches.
    This is similar to the `-C` option of _grep(1)_.

  * _config.commands.search.decode_latex_ = `False`:
    Whether searches should decode all LaTeX sequences.

  * _config.commands.search.decode_unicode_ = `False`:
    Whether searches should decode all Unicode characters.

  * _config.commands.search.fuzziness_ = `0`:
    How many fuzzy errors to allow during searches.
    Using this feature requires the optional `regex` dependency to be installed.

  * _config.commands.search.grep_ = `"grep"`:
    The command used to search the associated _files_ of entries in the database.
    The default tool (_grep(1)_) will not provide search results for attached PDF files, but other tools (such as [ripgrep-all](https://github.com/phiresky/ripgrep-all)) will.

  * _config.commands.search.grep_args_ = `[]`:
    Additional input arguments for the `config.commands.search.grep` command specified as a list of strings.
    Note, that GNU's _grep(1)_ understands extended regex patterns even without specifying `-E`.

  * _config.commands.search.ignore_case_ = `False`:
    Whether searches should be performed case-insensitive.

  * _config.commands.search.skip_files_ = `False`:
    Whether searches should skip looking through associated _files_ using `config.commands.search.grep`.

  * _config.commands.search.skip_notes_ = `False`:
    Whether searches should skip looking through associated _notes_.
    Note, that _notes_ are searched directly with Python rather than through an external system tool.

#### COMMANDS.SHOW

  * _config.commands.show.encode_latex_ = `True`:
    Whether non-ASCII characters should be encoded using LaTeX sequences.

#### DATABASE

  * _config.database.cache_ = `"~/.cache/cobib/databases/"`:
    The path under which to store already parsed databases.
    Set this to `None` to disable this functionality entirely.
    See also _cobib-database(7)_.

  * _config.database.file_ = `"~/.local/share/cobib/literature.yaml"`:
    The path to the database YAML file.
    You can use a `~` to represent your `$HOME` directory.
    See also _cobib-database(7)_.

  * _config.database.git_ = `False`:
    Whether to enable the _git(1)_ integration, see also _cobib-git(7)_.

#### DATABASE.FORMAT

  * _config.database.format.author_format_ = `AuthorFormat.YAML`:
    How the `author` field of an entry gets stored.

    The `cobib.config.config.AuthorFormat` object is an `Enum` representing the following options:<br>
        - `YAML`: store the title, first, and last names separately for each author.<br>
        - `BIBLATEX`: keep the information of all authors as plain text.

  * _config.database.format.label_default_ = `"{unidecode(label)}"`:
    The default format for the entry `label`s.

    This setting follows the _Python f-string_-like formatting of modifications (see also _cobib-modify(1)_).
    The default simply takes the originally set `label` and passes it through [text-unidecode](https://pypi.org/project/text-unidecode/), replacing all Unicode symbols with pure ASCII ones.
    A more useful example is `"{unidecode(author[0].last)}{year}"` which takes the surname of the first author
    (assuming `config.database.format.author_format = AuthorFormat.YAML`),
    replacing all Unicode characters with ASCII, and immediately appends the `year`.

  * _config.database.format.label_suffix_ = `("_", LabelSuffix.ALPHA)`:
    The suffix format used to disambiguate labels if a conflict would occur.

    The value of this setting is a pair:<br>
    The first element is the string used to separate the base label from the enumerator; by default, an underscore is used.<br>
    The second element is one of the `Enum` values of `cobib.config.config.LabelSuffix`:<br>
        - `ALPHA`: a, b, ...<br>
        - `CAPITAL`: A, B, ...<br>
        - `NUMERIC`: 1, 2, ...

  * _config.database.format.suppress_latex_warnings_ = `True`:
    Whether to ignore LaTeX warning during the escaping of special characters.
    This setting gets forwarded to the internally used [pylatexenc](https://pypi.org/project/pylatexenc/) library.

  * _config.database.format.verbatim_fields_ = `["file", "url"]`:
    Which fields should be left verbatim and, thus, remain unaffected by any special character conversions.

#### DATABASE.STRINGIFY

  * _config.database.stringify.list_separator.file_ = `", "`:
    The string used to concatenate the entries in _list_-type the `file` field of an entry when exporting to the BibTeX format.

  * _config.database.stringify.list_separator.tags_ = `", "`:
    The string used to concatenate the entries in _list_-type the `tags` field of an entry when exporting to the BibTeX format.

  * _config.database.stringify.list_separator.url_ = `", "`:
    The string used to concatenate the entries in _list_-type the `url` field of an entry when exporting to the BibTeX format.

#### EVENTS

_cobib-event(7)_ hooks get stored in `config.events` but it should **NOT** be modified directly!
Instead, the `Event.subscribe` decorator should be used (cf. _cobib-event(7)_).

### LOGGING

  * _config.logging.cache_ = `"~/.cache/cobib/cache"`:
    The default location of the cache.

  * _config.logging.logfile_ = `"~/.cache/cobib/cobib.log"`:
    The default location of the logfile.

  * _config.logging.version_ = `"~/.cache/cobib/version"`:
    The default location of the cached version number, based on which _cobib(1)_ shows you the latest changelog after an update.
    Set this to `None` to disable this functionality entirely.

#### PARSERS

#### PARSERS.BIBTEX

  * _config.parsers.bibtex.ignore_non_standard_types_ = `False`:
    Whether to ignore non-standard BibTeX entry types.

#### PARSERS.YAML

  * _config.parsers.yaml.use_c_lib_yaml_ = `True`:
    Whether to use the C-based implementation of the YAML parser.
    This **significantly** improves the performance but may require additional installation steps.
    See the [ruamel.yaml installation instructions](https://yaml.dev/doc/ruamel.yaml/install/) for more details.

#### THEME

  * _config.theme.theme_ = `"textual-dark"`:
    Textual's underlying `ColorSystem`.

    This setting can either be the name of one of textual's `BUILTIN_THEMES` or an instance of `textual.theme.Theme`.
    For a detailed guide, see [textual's documentation](https://textual.textualize.io/guide/design), but here is simple example to add an intense splash of color:
       ```python
       from textual.theme import BUILTIN_THEMES

       a_splash_of_pink = BUILTIN_THEMES["textual-dark"]
       a_splash_of_pink.primary = "#ff00ff"
       config.theme.theme = a_splash_of_pink
       ```

#### THEME.SEARCH

  * _config.theme.search.label_ = `"blue"`:
    The `rich.style.Style` used to highlight the labels of entries that matched a search.

    See [rich's documentation](https://rich.readthedocs.io/en/latest/style.html) for more details.

  * _config.theme.search.query_ = `"red"`:
    The `rich.style.Style` used to highlight the actual matches of a search query.

    See [rich's documentation](https://rich.readthedocs.io/en/latest/style.html) for more details.

#### THEME.SYNTAX

  * _config.theme.syntax.background_color_ = `None`:
    The background color used to display any `rich.syntax.Syntax` elements.

    If this is `None`, its default behavior will try to ensure a _transparent_ background.
    When running in the CLI, this implies a value of `"default"`; inside the TUI, textual's _$panel_ color variable is used.
    See [textual's documentation](https://textual.textualize.io/guide/design/#base-colors) for more details.

  * _config.theme.syntax.line_numbers_ = `True`:
    Whether to show line numbers in `rich.syntax.Syntax` elements.

    This setting is ignored in side-by-side diff views, where line numbers will **always** show.

  * _config.theme.syntax.theme_ = `None`:
    The theme used to display any `rich.syntax.Syntax` elements.

    If this is `None`, it defaults to `"ansi_dark"` or `"ansi_light"`, in-line with the main textual theme.
    Otherwise, this should be the name of a supported pygments theme.
    See [rich's documentation](https://rich.readthedocs.io/en/latest/syntax.html#theme) for more details.

#### THEME.TAGS

It is possible to configure special highlighting (or _markup_) for entries with certain _tags_.
The `TagMarkup` is a pair of an integer, indicating the priority (higher values take precedence),
and a string describing the `rich.style.Style`.

  * _config.theme.tags.high_ = `TagMarkup(40, "on bright_red")`:
    The markup for entries with the `high` tag.

  * _config.theme.tags.low_ = `TagMarkup(20, "bright_yellow")`:
    The markup for entries with the `low` tag.

  * _config.theme.tags.medium_ = `TagMarkup(30, "bright_red")`:
    The markup for entries with the `medium` tag.

  * _config.theme.tags.new_ = `TagMarkup(10, "bold bright_cyan")`:
    The markup for entries with the `new` tag.

    Note, that this tag does **not** get added automatically.
    But you can do so by subscribing to the _PostAddCommand_ event (see also _cobib-event(7)_):
       ```python
       from cobib.config import Event

       @Event.PostAddCommand.subscribe
       def add_new_tag(cmd: AddCommand) -> None:
           for entry in cmd.new_entries.values():
               if "new" not in entry.tags:
                   entry.tags = entry.tags + ["new"]
       ```

  * _config.theme.tags.user_tags_ = `{}`:
    A dictionary mapping _tag_ names to `TagMarkup` values.

    The _tags_ must be lower case, start with a letter, and only contain letters or the characters `.`, `-`, or `_`.

#### TUI

  * _config.tui.preset_filters_ = `[]`:
    A list of preset _cobib-filter(7)_ arguments available for quick access in the TUI.
    The first 9 entries of this list can be triggered by pressing the corresponding number in the TUI.
    Pressing `0` resets the filter to the standard list view.

    Each entry of this list should be a string describing a _cobib-filter(7)_, for example:
       ```python
       config.tui.preset_filters = [
           "++tags new",   # filters entries with the `new` tag
           "++year 2023",  # filters entries from the year 2023
       ]
       ```

  * _config.tui.scroll_offset_ = `2`:
    The minimum number of lines to keep above and below the cursor in the TUI's list view.
    This is similar to Vim's `scrolloff` option.

  * _config.tui.tree_folding_ = `(True, False)`:
    The default folding level of the tree nodes in the TUI's search result view.
    The two booleans fold the node of each matching entry and all its containing search matches, respectively.

#### UTILS

  * _config.utils.file_downloader.default_location_ = `"~/.local/share/cobib/"`:
    The default location for associated files that get downloaded automatically.

  * _config.utils.file_downloader.url_map_ = `{}`:
    A dictionary of _regex patterns_ mapping from article URLs to its corresponding PDF.

    Populating this dictionary will improve the success rate of the automatic file download.
    You can find more examples in the [wiki](https://gitlab.com/cobib/cobib/-/wikis/File-Downloader-URL-Maps), but here is a simple one:
       ```python
       config.utils.file_downloader.url_map[
           r"(.+)://quantum-journal.org/papers/([^/]+)"
       ] = r"\1://quantum-journal.org/papers/\2/pdf/"
       ```

  * _config.utils.journal_abbreviations_ = `[]`:
    A list of _journal abbreviations_ as pairs like `("full journal name", "abbrev. name")`.
    The abbreviated version should contain all the necessary punctuation (see also _cobib-export(1)_).

    You can find some examples in the [wiki](https://gitlab.com/cobib/cobib/-/wikis/Journal-Abbreviations).


## ENVIRONMENT

  * _$COBIB_CONFIG_:
    Disables the loading of a configuration file if set to one of the following values:
    `""`, `0`, `"f"`, `"false"`, `"nil"`, `"none"`.

  * _$EDITOR_:
    Specifies the editor program to use for the _cobib-edit(1)_ command.
    Hard-coding the `config.commands.edit.editor` option can overwrite this behavior.

## FILES

  * _~/.cache/cobib/cache_:
    The default file containing a basic cache, configured via `config.logging.cache`.

  * _~/.cache/cobib/cobib.log_:
    The default file of the log, configured via `config.logging.logfile`.

  * _~/.cache/cobib/databases/_:
    The default folder of the cache of parsed database files, configured via `config.database.cache`.

  * _~/.cache/cobib/version_:
    The default file of the version cache, configured via `config.logging.version`.

  * _~/.local/share/cobib/_:
    The default folder for the automatically downloaded associated files, configured via `config.utils.file_downloader.default_location`.

  * _~/.local/share/cobib/literature.yaml_:
    The default file of the database, configured via `config.database.file`.

## EXAMPLES

An example configuration which keeps all settings on their defaults can be generated using:
```bash
cobib _example_config
```
This prints the example configuration to _stdout_.

If you want to dump it to a file, you can redirect the output like so:
```bash
cobib _example_config > ~/.config/cobib/config.py
```

If you want to see an example in proper Python syntax, you can simply read the output or use a pager like so:
```bash
cobib _example_config | less
```

## SEE ALSO

_cobib(1)_, _cobib-database(7)_, _cobib-event(7)_, _cobib-git(7)_

[//]: # ( vim: set ft=markdown tw=0: )
