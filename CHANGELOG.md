# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [4.5.0] - 2024-03-17

Pypi: https://pypi.org/project/cobib/4.5.0/

### Added
- the new `cobib.utils.context.get_active_app` method which returns any running
  textual App and replaces the need for the `cobib.utils.prompt.Prompt.console`
  and `cobib.utils.progress.Progress.console` (which have been removed) (!137)
- `cobib.parsers.YAMLParser.parse` can now also parse strings directly (rather
  than always interpreting the argument as the path to a file) (!137)
- the `review` command (#131,!137).
  Please refer to its online documentation or the man-page for more details on
  how to use it.
- the `cobib.database.Entry.merge` method (!137)

### Changed
- log messages will now be displayed in the `LogPanel` of the TUI (which can be
  toggled with the `z` keybinding) (#132,!133)
- the `cobib.ui.components.prompt` module has been refactored into `cobib.utils.prompt` (!133)

### Deprecated
- the `console` argument to all commands has been deprecated since it no longer
  has any effect (!133)
- the `prompt` argument to all commands has been deprecated since it no longer
  has any effect (!133)
- access to the following `shell_helper` commands will change in the next release:
  - `cobib _lint_database` will become `cobib lint`
  - `cobib _unify_labels` will become `cobib unify_labels`
  - `cobib _example_config` will become `cobib example_config`

### Fixed
- loading a cached database will be bypassed during `_lint_database` (#133)
  - to support this the `bypass_cache` keyword-argument was added to the
    `Database.read` method

### Removed
- official Windows support label. It _might_ work but no guarantees are made (#136)


## [4.4.0] - 2023-12-15

Pypi: https://pypi.org/project/cobib/4.4.0/

### Added
- a primitive caching mechanism to speed up the database loading. This feature
  is enabled by default and will store its cache at `~/.cache/cobib/databases/`.
  You can configure the location via `config.database.cache` or even disable
  caching entirely by changing this setting to `None`. (see also #129 and !108)
- added the `-r/--remove` option to the `modify` command (#128)
  - this can achieve the opposite of `-a/--add` in the sense that it will try to
    remove the specified modification from a list or subtract a number from
    numeric values
  - other field types than lists or numbers are not supported by this option
- added the `-l/--limit` option to the `list` command (#127)
  - exposed the `ListCommand.sort_entries` method in the public API
  - added the `ListCommand.execute_dull` method in the public API
- the `search`, `export`, and `modify` commands now also support sorting and limiting options to be
  passed onto the `list` command (along with the already existing filtering options)
- the `config.tui.tree_folding` setting which allows you to configure the
  default folding state of the tree nodes in the TUI's search result view
- the `ENTER` binding in the TUI's search result view to recursively toggle all
  folds of the current node

### Changed
- when using the TUI you may now use the `:show <label>` command to jump to the
  specified label (#126,!116)
- the `search` command now reports its progress live (!117)

### Fixed
- unblocked the vertical scrollbar of the TUI's list view from the scroll offset


## [4.3.1] - 2023-11-12

Pypi: https://pypi.org/project/cobib/4.3.1/

### **Breaking Change**
Note, that the introduction of the detailed author information parsing in v4.3.0
resulted in possible breaking of a custom `config.database.format.label_default`
setup. This bugfix release is meant to emphasize this breaking change and
updates the documented example in the example configuration file. For the sake
of verbosity, here is the change applied to the example:

- old: `"{unidecode(author.split(' and ')[0].split()[-1])}{year}"`
- new: `"{unidecode(author[0].last)}{year}"`


## [4.3.0] - 2023-11-12

Pypi: https://pypi.org/project/cobib/4.3.0/

### Prelude

#### Detailed Authors
coBib now has the ability to store more detailed author information (see #92 and
!88). This means, that the `author` field of an entry is analyzed in more detail
and coBib will separate out the first and last names as well as name pre- and
suffixes. The new setting `config.database.format.author_format` determines,
whether this detailed information is kept directly in the database (the
`AuthorFormat.YAML` setting; the **new default**) or is only constructed at
runtime and the author field is still simply saved in BibLaTeX form
(`AuthorFormat.BIBLATEX`).

Note, that the `YAML` format also implies, that Unicode characters are allowed
and will *not* be encoded in LaTeX form. This has an effect on how you may need
to format your searches. See also #130 for some more insights on this.

If you have company names or any author name which you want to have treated
verbatim, you can simply wrap it in curly braces (e.g. `{My Company}`).
Refer to the online documentation of `cobib.database.Author` and the above
setting for more details.

#### Wiki
coBib now has a [Wiki](https://gitlab.com/cobib/cobib/-/wikis/home) where we can
gather useful configuration resources and other details which may not make it
into the full documentation.

For example, if you are interested in the tracking more metadata of your
database (as suggested in #123), be sure to check out
[this wiki page](https://gitlab.com/cobib/cobib/-/wikis/Useful-Event-Hooks)!

### Added
- the `-f` short-hand alias for the `--field` argument of the `open` command
- the `opened_entries` attribute of the `OpenCommand` (which is accessible during the `PostOpenCommand` hook)
- the new `git` command to simplify running git operations on the database (#124)
- new bindings for `Home`, `End`, `PageUp`, and `PageDown` in the TUI
- (DEV) added a new `DEPRECATED` logging level which has value 45
- Python 3.12 is now officially tested and supported
- the `config.commands.show.encode_latex` setting
- the `encode_latex` attribute to the `BibtexParser`
- the `config.database.format.verbatim_fields` setting
- the `config.database.format.author_format` setting. The new default behavior
  is to store detailed author information in YAML form.
- the `encode_latex` keyword-argument to the `Entry.stringify` method
- the `Entry.formatted` method. This replaces the `Entry.escape_special_chars` method.

### Changed
- an error will be logged when a file is not found during the `open` command
- the following commands are now treated specially when run via the `:` prompt of the TUI:
  - `init`: will log an error
  - `git`: will log an error
  - `show`: will log a warning

### Deprecated
- The `LabelSuffix.CAPTIAL` value because it was misspelled. Please use `LabelSuffix.CAPITAL` instead.

### Fixed
- non-asynchronous commands triggered via the `:` prompt of the TUI will no longer break it (#125)
- ensure UTF-8 encoding is used for downloaded data (this fixes many odd encounters w.r.t. special characters)
- the spelling of the `LabelSuffix.CAPITAL` value (it used to be spelled `LabelSuffix.CAPTIAL`)

### Removed
- the `Entry.escape_special_chars` method. Use `Entry.formatted` instead.


## [4.2.0] - 2023-08-08

Pypi: https://pypi.org/project/cobib/4.2.0/

### Added
- added the `config.tui.scroll_offset` setting
- added the `--field` command line option to the `open` command
- (DEV) added a new `HINT` logging level which has value 35 and thus allows to
  provide information to the user with a higher priority than `WARNING`
- added the new `config.tui.preset_filters` (#114)
  - preset filters can be selected from the TUI via the `p` key binding
  - the first 9 filters can be selected directly by pressing the respective number
  - pressing `0` resets any applied filter
- implemented special tags (#63,!83)
  - adds new builtin tags which will trigger special highlights of entries: `new`, `high`, `medium`, `low`
  - adds the new `config.theme` settings section for configuring these settings
  - you can also add more special tags via `config.theme.tags.user_tags`
- added the `--skip-files` command line option to the `search` command

### Changed
- unicode symbols in entry labels will now be replaced with ascii ones (#119,#120)
  - this is configured via the `config.database.format.default_label` setting, so if you are using a
    custom value for this, be sure to update your config to make use of this feature
- some user-visible logging messages around label disambiguation have been added (see also #121)
- a warning has been added when the YAML parser encounters identical labels (which normally should
  not occur in the database but if it does, coBib does not really know how to resolve this)
- DOI redirect links are now followed recursively (up to 3 times), improving PDF
  download link detection in the process (#97)

### Deprecated
- the `config.commands.search.highlights` section is deprecated in favor of `config.theme.search`

### Fixed
- retain scroll position in the TUI's list view


## [4.1.0] - 2023-06-11

Pypi: https://pypi.org/project/cobib/4.1.0/

### Added
- added the following settings which specify whether or not to preserve
  associated files during the respective commands being run:
  - `config.commands.delete.preserve_files`
  - `config.commands.edit.preserve_files`
  - `config.commands.modify.preserve_files`
- added a confirmation prompt before deleting an entry (#110)
  - this prompt can be disabled by setting `config.commands.delete.confirm` to `False`
- added the `--no-ignore-case` (`-I` for short) command line options to the
  `list` and `search` command (#116)
- added the `--no-preserve-files` command line options to the `delete`, `edit`
  and `modify` command (#116)
- added the `config.commands.search.context` setting which configures the
  default number of context lines to be provided for search query matches
- added more options to configure the automatic download behavior:
  - the new `config.commands.add.skip_download` setting
  - the new `--force-download` option of the `add` command
  - the new `config.commands.import_.skip_download` setting
  - the new `--force-download` option of the `import` command
- the user is asked for confirmation when quitting the TUI (!71)

### Changed
- refactored the TUI by leveraging textual's `Screen` concept (#111,!71)
  - this means the TUI will look slightly different but no real functional change has occurred
  - the view of an `Entry` can now be scrolled when the output exceeds the available space
- switched from the `BeautifulSoup` HTML parser to `lxml`
  - this is supposed to give more accurate results but adds an extra dependency

### Deprecated
- The following shell helpers are no longer used with the zsh completion being
  removed. Thus, these methods will be removed in the future:
  - `cobib _list_commands`
  - `cobib _list_filters`
  - `cobib _list_labels`
  - If you see warnings because of this while you are using the CLI, you
    probably still have the (now removed) zsh completion script installed. You
    should remove the `_cobib` file which will be located in one of the
    directories listed in your `$FPATH` environment variable.

### Fixed
- the proper pre-population of the TUI prompt during the sorting action (#117)
- preserves the value of `config.commands.list_.default_columns` and
  properly removes a field if it is no longer sorted by in the TUI (#117)
- properly updates the list of entries in the TUI after changing the database contents;
  for example via `add` (#113) or `delete` (#113) or `edit` (#118)
- an issue where file-accessing operations performed on a newly added entry within
  the same TUI session would fail because the path would not be iterated correctly
- the live updating of the download progress bar inside the TUI (#112)

### Removed
- the crude and very slow zsh completion script


## [4.0.0] - 2023-05-20

Pypi: https://pypi.org/project/cobib/4.0.0/

### **Breaking Changes**
- Configuration settings can no longer be set by item access and instead must
  use attribute syntax. For example you need to change:
  ```python
  config["database"]["git"] = True
  ```
  to
  ```python
  config.database.git = True
  ```
  - the `config.commands.list` section had to be renamed to `config.commands.list_`
  - the `config.tui` section has been entirely removed
- The `cobib.commands.list` module was moved to `cobib.commands.list_`.
- The function signature of all command- and importer-related events has changed!
  For more details please refer to the
  [online documentation](https://cobib.gitlab.io/cobib/cobib/config/event.html).

### Added
- Python 3.11 is now officially tested and supported
- Full rewrite of all commands to use `rich` for a nicer CLI (#78,!51)
- Full rewrite of the TUI based on `textual` (#78,!51)
- the `--disambiguation` argument of the `add` command (#99,!58)
- the `--ignore-case` argument of the `list` command (#105)
  - this also comes with the new `config.commands.list_.ignore_case` setting
- the `search` command now accepts multiple query strings at once which will be
  searched over independently (#106)

### Changed
- the new default value of `config.parsers.yaml.use_c_lib_yaml` is now `True` as announced in version [3.4.0]
- refactored the entire config as a dataclass (!63)
  - this implies that settings can only be set via attributes
  - but as a benefit the maintainability and documentation have improved significantly
- The function signature of all command-related events has changed! Please refer to the
  [online documentation](https://cobib.gitlab.io/cobib/cobib/config/event.html)
  for more details. (!63)
- The function signature of all importer-related events has changed! Please refer to the
  [online documentation](https://cobib.gitlab.io/cobib/cobib/config/event.html)
  for more details. (!66)
- the API of the `cobib.commands` and `cobib.importers` module has been improved (!64)
  - this should not have any end-user facing effects
- the `cobib.commands.list` module was moved to `cobib.commands.list_`

### Deprecated
- the `--update` argument of the `add` command is deprecated in favor of `--disambiguation update`
- the `--skip-existing` argument of the `add` command is deprecated in favor of `--disambiguation keep`

### Fixed
- the detection whether an entry already exists broke when label disambiguation was added in [3.3.0]
  and is now fixed by means of an interactive prompt during the `add` command

### Removed
- the warning triggered upon setting `config.database.format.month` which got removed in [3.1.0]
- Python 3.7 is no longer supported


## [3.5.5] - 2023-04-11

Pypi: https://pypi.org/project/cobib/3.5.5/

### Fixed
- opening of non-list type fields (#100)


## [3.5.4] - 2022-12-26

Pypi: https://pypi.org/project/cobib/3.5.4/

### Fixed
- missing files encountered during searching will log warnings gracefully instead of harshly
- handle newline characters in the TUI (#98)


## [3.5.3] - 2022-11-16

Pypi: https://pypi.org/project/cobib/3.5.3/

### Fixed
- incorrect author concatenation in ISBN Parser
- using the disambiguated label for the names of downloaded files (#96)


## [3.5.2] - 2022-05-22

Pypi: https://pypi.org/project/cobib/3.5.2/

### Fixed
- run TUI on BSD platforms (!52)


## [3.5.1] - 2022-04-25

Pypi: https://pypi.org/project/cobib/3.5.1/

### Fixed
- safely check cache existence before attempting to write (#94)


## [3.5.0] - 2022-01-13

Pypi: https://pypi.org/project/cobib/3.5.0/

### **News:** coBib v4.0 will come with a new UI!
The plan is to switch to [rich][rich] and [textual][textual] instead of the current curses TUI.
This will open up some great possibilities for a much more modern UI.

However, this change will require some *major* refactoring including breaking changes of the API
and some of the user configuration options. It will also be a rather drastic change in style.
Thus, I will attempt to support v3.5 with bugfix releases until 1.1.2023

It will likely take a few months until v4.0 gets released but I am starting development on it now.
You can follow the progress here: <https://gitlab.com/cobib/cobib/-/issues/78>

[rich]: https://github.com/Textualize/rich
[textual]: https://github.com/Textualize/textual

### Added
- the configuration loading can be disabled via the environment variable `COBIB_CONFIG`
    - values which disable the loading entirely are: `"", 0, f, false, nil, none`
    - you can also specify a custom path to a configuration file in this variable

### Removed
- the `INI`-style configuration got fully removed (as deprecated in [3.0.0] - 2021-04-10)


## [3.4.0] - 2021-12-01

Pypi: https://pypi.org/project/cobib/3.4.0/

- coBib now requires the `requests-oauthlib` package
    - technically this is an optional dependency for now, but it will likely become a requirement soon

### Added
- the new `config.parsers.yaml.use_c_lib_yaml` setting which significantly improves loading performance
    - this setting will change its default value to `True` in version 4.0.0
* the `Import` command (#86,!49):
    - can be used to import libraries from other bibliography managers (see next bullet)
    - see `cobib import --help` for more information
- the `cobib.importers` module:
    - provides importer classes for various other bibliography managers
    - these get registered at runtime under the `cobib import` command
    - this release provides the `--zotero` importer
    - see `cobib import --zotero -- --help` for more information
- the `config.logging.cache` option, specifying the location of a simple json cache
- the `config.commands.open.fields` option, specifying the names of the data fields which are checked for openable URLs (#89)

### Changed
- the `PreFileDownload` event now takes an additional argument: `headers: Optional[Dict[str, str]]`

### Fixed
- downloaded file names will not duplicate the `.pdf` suffix


## [3.3.2] - 2021-11-17

Pypi: https://pypi.org/project/cobib/3.3.2/

### Fixed
- re-enable the terminal keypad during resize event
    - this ensures proper arrow-key behavior after returning from an external editor
- clear screen after closing TUI to remove all screen artifacts

### Security
- remove warning when using the DOI parser because the upstream issue related to #91 got fixed


## [3.3.1] - 2021-10-19

Pypi: https://pypi.org/project/cobib/3.3.1/

### Fixed
- erroneous label disambiguation of Entry labels which already conform with `config.database.format.default_label_format` (#87,!47)
- do not add empty file list when unifying database

### Security
- log warning when using the DOI parser because of (#91)


## [3.3.0] - 2021-10-04

Pypi: https://pypi.org/project/cobib/3.3.0/

### Added
- print Changelog since the last run version (cached in `config.logging.version`) (#82)
- the `AddCommand` now has a new `--update` option (#79,!41)
- the `_lint_database` utility now takes the `--format` argument, which automatically resolves all lint messages (#81,!42)
- the new `URLParser` (available via `cobib add --url <URL>` (#84,!44)
    - it attempts importing from a plain URL
    - simultaneously the arXiv, DOI, and ISBN parsers now also support URL containing a matching identifier directly
- the `--dry` argument of the `ModifyCommand` to prevent errors during large bulk modifications
* the `config.database.format.label_default` and `config.database.format.label_suffix` options (#85,!45)
    - labels will automatically be formatted according to the default option
    - if labels conflict with existing ones, the suffix option will be used for disambiguation
    - the `AddCommand` has a new `--skip-existing` option which disables automatic label disambiguation
    - use `cobib _unify_labels --apply` to unify all labels in your database
- subscribable events (#71,!46)
    - allows registering of hooks to be executed in certain situation
    - more information is provided at the [online documentation](https://cobib.gitlab.io/cobib/cobib/config/event.html)

### Changed
- when an unknown variable is encountered in the modification of the `modify` command it falls back to an empty string rather than the name of the attempted variable

### Removed
- the `-s` option of the `AddCommand` is no longer available. You need to write out `--skip-download`
- the `ID` filter argument on the `list` command (deprecated in v3.2.0 in favor of the `label` filter)


## [3.2.1] - 2021-07-15

Pypi: https://pypi.org/project/cobib/3.2.1/

### Fixed
- when adding multiple entries at once, continue adding after encountering a single duplicate (#83)


## [3.2.0] - 2021-06-26

Pypi: https://pypi.org/project/cobib/3.2.0/

### Added
- basic auto-downloading of PDF files for arXiv IDs and configured DOIs (#25,!35,!39):
    - the default download location can be configured via `config.utils.file_downloader.default_location`
    - on a per addition basis, this default can be overwritten via the `--path` keyword option of the `AddCommand`
    - if a file already exists in this location of the file system, the download will be skipped
    - download for DOI entries must configure URL patterns in `config.utils.file_downloader.url_map`
    - on a per addition basis, the entire automatic download can be skipped with `--skip-download`
- automatic journal abbreviations (#62,!36):
    - users can configure a list of journal abbreviations via `config.utils.journal_abbreviations`
    - if present, coBib will store the journal in its elongated form
    - a user can then automatically convert to abbreviated forms during exporting (see the new `--abbreviate` and `--dotless` arguments)
- Tentative Windows support by disabling the TUI
- a `--preserve-files` argument was added to the following commands. Unless it is given, these will delete/rename associated files of affected entries:
    - `DeleteCommand`
    - `EditCommand`
    - `ModifyCommand`

### Changed
- the `modifications` of a `ModifyCommand` get interpreted as f-strings (#77,!37):
    - available variables are the entry's label and data fields
- any `ListCommand` filter gets interpreted as a regex pattern (#76)

### Deprecated
- the `ID` filter argument was fully replaced by `label`, unifying the CLI API. Support will be dropped in v3.3.0

### Fixed
- Removed (most) duplication of log messages


## [3.1.1] - 2021-05-25

Pypi: https://pypi.org/project/cobib/3.1.1/

### Fixed
- Pypi package metadata


## [3.1.0] - 2021-05-24

Pypi: https://pypi.org/project/cobib/3.1.0/

### Added
- the YAML format of the database has been extended to support the following: (#55)
    - numbers can be stored as integers
    - the `ID` field is no longer required and will be properly inferred from the label
    - the following fields can be stored as lists: `file`, `tags`, `url`
- three new configuration options were added to complement the above list format options:
    - `config.database.stringify.list_separator.file`
    - `config.database.stringify.list_separator.tags`
    - `config.database.stringify.list_separator.url`
- the `_lint_database` shell utility has been added which can be used to detect possible improvements for the database
- the append-mode of the `ModifyCommand` was implemented (#60):
    - specifying `-a`/`--add` will add the modification value to the field of the entries rather than overwrite it
    - this can be used for string or list concatenation and even number addition on numeric fields

### Changed
- use file paths relative to user-home (achieved by replacing `os.path` with `pathlib`) (#69)
- the shell helper `_list_tags` has been renamed to `_list_labels`
- (DEV): the `logging` and `zsh_helper` modules have been relocated to the `cobib.utils` package
- `+` symbols will no longer be stripped from tags (this was a left-over artifact from pre-v1.0.0)

### Deprecated
- the `config.database.format.month` setting is deprecated in favor of proper three-letter code encoding to support common citation style macros (!34)

### Fixed
- renaming the label during the `edit` command does not leave the previous label entry behind:
    - a followup also ensured that renaming entries happens in-place (#75)
- the sorting of the `list` command


## [3.0.0] - 2021-04-10

Pypi: https://pypi.org/project/cobib/3.0.0/

- From now on, `coBib` is the official way of spelling!

### Added
- coBib's documentation is now generated by [`pdoc`](https://pdoc.dev/) and hosted at https://cobib.gitlab.io/cobib/cobib.html
- (DEV): the `cobib.database.Database`-Singleton has been added to centrally manage the bibliographic runtime data (!28)
- the new option `config.database.format.suppress_latex_warnings`
- the new option `config.commands.edit.editor` which takes precedence over the `$EDITOR` variable

### Changed
- the `INI`-style configuration is replaced with a `Python`-based configuration (#54,!25)
    - for guidance on how to migrate an existing configuration please read https://mrossinek.gitlab.io/programming/cobibs-new-configuration/
- (DEV): `cobib.parser.Entry` has been moved to `cobib.database.Entry`
- the `cobib.parsers` module has been extracted (prep for #49, !28)
- the filenames of the associated files are preserved when exporting to a Zip file
- when trying to add an entry with an existing label, the database is not written to and a warning is raised early
- month conversion and special character escaping are only done upon saving entries to the database
- the path to the default logfile can now be configured via `config.logging.logfile` and defaults to `~/.cache/cobib/cobib.log`

### Deprecated
- the `INI`-style configuration is deprecated
    - new configuration options will not be added to this style
    - only bugs which fully break usability will be fixed with regards to this configuration style
    - legacy-support will be fully removed on 1.1.2022

### Fixed
- the ZSH helper utilities now respect the `-c`, `-l`, and `-v` command line options
- the `RedoCommand` should only revert a previously `UndoCommand` operation (#65)
- the `SearchCommand` got some contexts improvements and correctly splits grep results
- unwrapping does not crash the TUI if the cursor was multiple lines below the new buffer height
- line continuation guides are not swallowed by current line highlighting
- ensure the TUI's top line does not become negative
- the TUI's handler for resizing events
- `JSONDecodeError`s thrown by the `ISBNParser` are caught and handled gracefully

### Removed
- the functions `read_database()` and `write_database()` are no longer available (!28)


## [2.6.1] - 2021-02-05

Pypi: https://pypi.org/project/cobib/2.6.1/

Note: [2.6.1] was not released from the `master`-branch, which resulted in a non-linear development.

### Changed
- `init --git` will not initialize a repository unless git has configured both, `name` and `email`

### Fixed
- TUI no longer crashes when aborting to quit (#64)


## [2.6.0] - 2020-12-31

Pypi: https://pypi.org/project/cobib/2.6.0/

### Added
- Git integration (#44, !20):
    - will automatically track any changes done to the database file with git
    - must be enabled by setting the `DATABASE/git` option to `True` **and** running `cobib init --git`
    - Note, that you must have at least set a `name` and `email` in the git config!
- Undo/Redo commands to operate on git history of the database (#59,!23)
    - for obvious reasons these commands require the Git integration (see above) to be enabled
- the `Prompt` command inside of the TUI:
    - allows executing arbitrary CoBib CLI commands
    - the default key binding is `:`
- the `Modify` command: (#60,!24)
    - allows bulk modification of multiple entries in a `<field>:<value>` format
    - for now, this will **always** overwrite the field with the new value!
    - an extension to appending values is planned for a later release
    - the set of entries to be modified can be specified just like with the `export` command through `list`-command filters or manual selection (by setting the `--selection` flag)

### Changed
- the viewport history is preserved correctly (#21,!22)
    - this allows performing a search while showing an entry and reverts back to the correct view after quitting the search
    - the changes mainly involved refactoring of the `cobib/tui` module
- the **positional** argument of the `modify` and `search` has been renamed internally from `list_arg` to `filter`
    - this should not have any visible effect to an end-user but may be relevant to developers

### Fixed
- gracefully handle multiple terminal sizing issues with regards to popups (#58)
- catch messages on `stdout` during deletion from TUI
- added missing help strings to the TUI help menu

### Removed
- The `--force` argument to the `init` command has now been removed (after being deprecated in v2.5.0).


## [2.5.0] - 2020-12-08

Pypi: https://pypi.org/project/cobib/2.5.0/

### Added
- support for multiple associated files (#42,!19)
- interactive menu when opening an entry with multiple associated files (!19)

### Deprecated
- The `--force` argument to the `init` command has been deprecated. I don't think there is any
  benefit to providing the user the option to nuke their database file from the CLI. Instead,
  they can simply edit the file manually.

### Fixed
- always store years as strings to be compatible with bibtexparser
- handle invalid arXiv or DOI IDs gracefully (#57)


## [2.4.1] - 2020-11-01

Pypi: https://pypi.org/project/cobib/2.4.1/

### Fixed
- ISBN parser was missing the ENTRYTYPE and did not use strings for number fields
- the ISBN parser can now handle empty entries (#53)
- the TUI will not crash on stdout/stderr messages exceeding the window width
- the TUI respects quoted strings in the prompt handler (#52)


## [2.4.0] - 2020-10-14

Pypi: https://pypi.org/project/cobib/2.4.0/

### Added
- the `FORMAT/default_entry_type` option used for manual entry addition
- a **manual** insertion mode available through `edit -a new_label` and `add -l new_label`
- a ISBN-based parser for adding new entries (#45)
- the TUI-based `select` command (and corresponding settings) (#8,!18)
- the `--selection` argument for the `export` command (!18)

### Changed
- TUI color highlighting is now prioritized (!17)

### Fixed
- support URLs in file field during `open` command (#47)
- the TUI no longer crashes when encountering long prompt inputs (#48)
- the `edit` command can handle labels which start with common substrings (#46)
- support multiple ANSI colors on a single line (#50)


## [2.3.4] - 2020-09-14

Pypi: https://pypi.org/project/cobib/2.3.4/

### Fixed
- another AUR package installation error


## [2.3.3] - 2020-09-14

Pypi: https://pypi.org/project/cobib/2.3.3/

### Fixed
- AUR package installation error

## [2.3.2] - 2020-09-10

Pypi: https://pypi.org/project/cobib/2.3.2/

### Added
- option to default to case-insensitive searching (`DATABASE/search_ignore_case`)

### Changed
- clearing the prompt, aborts the command execution

### Fixed
- search command correctly handles missing arguments in TUI (#43)

## [2.3.1] - 2020-09-10

Pypi: https://pypi.org/project/cobib/2.3.1/

### Fixed
- faulty Pypi package

## [2.3.0] - 2020-09-10

Pypi: https://pypi.org/project/cobib/2.3.0/

### Added
- Logging functionality has been added. The verbosity level can be controlled via `-v` (INFO) and `-vv` (DEBUG).
  As soon as the TUI starts, all logging output is redirected to `/tmp/cobib.log`.
- Command line argument `-l` or `--logfile` can be used to specify the output path of the log. This will overwrite the `/tmp/cobib.log` location.
- the `TUI/scroll_offset` setting was added. It defaults to `3` and behaves similar to Vim's `scrolloff` setting.
- Configuration validation has been added. This extends the logging functionality to support more runtime debug information.
- popup window support: stdout and stderr messages are presented in a popup similarly to the help window

### Changed
- `-v` command line argument now refers to `--verbose` rather than `--version`
- Performance of the `add` command has been improved by not refreshing the database when outside of the TUI.

### Fixed
- bug when resizing causes the window width to become greater than the buffer width (#39)
- do not escape special characters in labels (#40)
- avoid special character encoding in file paths

## [2.2.2] - 2020-08-13

Pypi: https://pypi.org/project/cobib/2.2.2/

### Fixed
- current line highlight if viewport is wider than buffer was not correctly reset
- the `ignore_non_standard_types` setting had no effect

## [2.2.1] - 2020-08-10

Pypi: https://pypi.org/project/cobib/2.2.1/

### Changed
- when wrapping the TUI lines, indent until after the label column (#26)
- renamed `default.ini` to `example.ini` in the documentation folder

### Fixed
- current line highlight after viewport width was not correctly reset
- correctly convert boolean configuration options (#34)
- fix crash of TUI in wrap command when viewport is empty (#37)
- default configuration settings are managed centrally and consistently (#35)


## [2.2.0] - 2020-07-12

Pypi: https://pypi.org/project/cobib/2.2.0/

### Added
- allow configuring the program used to `open` associated files
- prompt user before actually quitting CoBib (#33)
- implements the Search command (#7, !12)

### Fixed
- the default value of the `open` command was not set correctly


## [2.1.0] - 2020-06-14

Pypi: https://pypi.org/project/cobib/2.1.0/

### Added
- added half- and full-page scrolling (#22)

### Changed
- importing from `bibtex` data defaults to **not** ignored non-standard entry types (#28)
- suppress LaTex encoding warnings except when adding entries (#29)
- `Search` and `Select` print warnings to the prompt while not implemented

### Fixed
- `init` command ensures directory of database file exists
- remove window artifacts after `help` menu is closed (#20)
- configuration file detection was missing a user home expansion (#31)

## [2.0.0] - 2020-06-06

Pypi: https://pypi.org/project/cobib/2.0.0/

### Fixed
- respect sort order reversing and filter `XOR`ing from the TUI (#18)
- `edit` command on Mac OS (#19)

### Changed
- made `init` command safe against database overwriting
- TUI: list entries in reverse order by default (config: TUI/reverse_order)


## [2.0.0b4] - 2020-05-16

Pypi: https://pypi.org/project/cobib/2.0.0b4/

### Fixed
- reset viewport position when updating buffer


## [2.0.0b3] - 2020-05-16

Pypi: https://pypi.org/project/cobib/2.0.0b3/

### Fixed
- properly assert valid current line number


## [2.0.0b2] - 2020-05-16

Pypi: https://pypi.org/project/cobib/2.0.0b2/

### Fixed
- fixed TUI startup


## [2.0.0b1] - 2020-05-16

**Warning**: do NOT use! The TUI is broken in this release!

Pypi: https://pypi.org/project/cobib/2.0.0b1/

### Fixed
- TUI does not crash when opening an entry with no associated file
- correctly reset current line positions after filtering and editing


## [2.0.0b0] - 2020-04-28

Pypi: https://pypi.org/project/cobib/2.0.0b0/

### Changed
- _internal_: refactored the config into a class
- centralized the database handling to improve performance (#12,!9)

### Fixed
- the `Show` command does not break after scrolling the viewport (#13)


## [2.0.0a2] - 2020-04-27

Pypi: https://pypi.org/project/cobib/2.0.0a2/

### Added
- user configuration options for:
    - TUI colors
    - TUI key bindings
    - TUI default list arguments
- help window highlighting

### Changed
- sorting and filtering commands remain persistent when updating the list view


## [2.0.0a1] - 2020-04-23

Pypi: https://pypi.org/project/cobib/2.0.0a1/

### Added
- Added a basic curses-based TUI (#5,!7)

### Changed
- _internal_: refactored commands into separate module


## [1.1.0] - 2020-03-28

Pypi: https://pypi.org/project/cobib/1.1.0/

### Added
- add `FORMAT.month` configuration option to configure the default type for
    month fields (defaults to `int`) (#3,!4)
- escape special LaTeX characters (#2,!5)

### Fixed
- `list` no longer breaks with a `KeyError` when a queried field does not exist
    in any bibliography entry (!2)
- `--label` can now correctly overwrite the ID (#4,!3)

### Changed
- `set_config()` and global `CONFIG` exported to separate module


## [1.0.2] - 2020-01-12

Pypi: https://pypi.org/project/cobib/1.0.2/

Note: this removal is not seen as a MINOR version bump because this is
      essentially a long out-standing bug fix

### Removed/Fixed
- doi extraction from pdf files (476efc4f)
  - also removes the ability to add entries directly via pdf files


## [1.0.1] - 2020-01-12

Pypi: https://pypi.org/project/cobib/1.0.1/

### Changed
- metadata for pypi


## [1.0.0] - 2020-01-12

First MAJOR release. Also available via Pypi: https://pypi.org/project/cobib/1.0.0/
The project was renamed from `CReMa` to `CoBib`

### Added
- allow sorting the list output (2a5a94f1)
- crude and slow (!!!) zsh completion (9f28f441)
- support Darwin's `open` command

### Changed
- suppress list output when exporting
- add used tags to columns when listing
- sort YAML database entries by keys (d2af42d2)

### Fixed
- fixed arxiv parser (7ce3726f)


## [0.2] - 2019-09-02

Note: this release was not marked MAJOR because this is still a WIP and early
      alpha release.

### Added
- complete rewrite to use a plain-text `yaml` database instead of `sqlite3` !1

### Removed
- `sqlite3` database


## [0.1] - 2019-04-29

### Added
- initial version with a basic `sqlite3`-based database


[Unreleased]: https://gitlab.com/cobib/cobib/-/compare/v4.5.0...master
[4.5.0]: https://gitlab.com/cobib/cobib/-/tags/v4.5.0
[4.4.0]: https://gitlab.com/cobib/cobib/-/tags/v4.4.0
[4.3.1]: https://gitlab.com/cobib/cobib/-/tags/v4.3.1
[4.3.0]: https://gitlab.com/cobib/cobib/-/tags/v4.3.0
[4.2.0]: https://gitlab.com/cobib/cobib/-/tags/v4.2.0
[4.1.0]: https://gitlab.com/cobib/cobib/-/tags/v4.1.0
[4.0.0]: https://gitlab.com/cobib/cobib/-/tags/v4.0.0
[3.5.5]: https://gitlab.com/cobib/cobib/-/tags/v3.5.5
[3.5.4]: https://gitlab.com/cobib/cobib/-/tags/v3.5.4
[3.5.3]: https://gitlab.com/cobib/cobib/-/tags/v3.5.3
[3.5.2]: https://gitlab.com/cobib/cobib/-/tags/v3.5.2
[3.5.1]: https://gitlab.com/cobib/cobib/-/tags/v3.5.1
[3.5.0]: https://gitlab.com/cobib/cobib/-/tags/v3.5.0
[3.4.0]: https://gitlab.com/cobib/cobib/-/tags/v3.4.0
[3.3.2]: https://gitlab.com/cobib/cobib/-/tags/v3.3.2
[3.3.1]: https://gitlab.com/cobib/cobib/-/tags/v3.3.1
[3.3.0]: https://gitlab.com/cobib/cobib/-/tags/v3.3.0
[3.2.1]: https://gitlab.com/cobib/cobib/-/tags/v3.2.1
[3.2.0]: https://gitlab.com/cobib/cobib/-/tags/v3.2.0
[3.1.1]: https://gitlab.com/cobib/cobib/-/tags/v3.1.1
[3.1.0]: https://gitlab.com/cobib/cobib/-/tags/v3.1.0
[3.0.0]: https://gitlab.com/cobib/cobib/-/tags/v3.0.0
[2.6.1]: https://gitlab.com/cobib/cobib/-/tags/v2.6.1
[2.6.0]: https://gitlab.com/cobib/cobib/-/tags/v2.6.0
[2.5.0]: https://gitlab.com/cobib/cobib/-/tags/v2.5.0
[2.4.1]: https://gitlab.com/cobib/cobib/-/tags/v2.4.1
[2.4.0]: https://gitlab.com/cobib/cobib/-/tags/v2.4.0
[2.3.4]: https://gitlab.com/cobib/cobib/-/tags/v2.3.4
[2.3.3]: https://gitlab.com/cobib/cobib/-/tags/v2.3.3
[2.3.2]: https://gitlab.com/cobib/cobib/-/tags/v2.3.2
[2.3.1]: https://gitlab.com/cobib/cobib/-/tags/v2.3.1
[2.3.0]: https://gitlab.com/cobib/cobib/-/tags/v2.3.0
[2.2.2]: https://gitlab.com/cobib/cobib/-/tags/v2.2.2
[2.2.1]: https://gitlab.com/cobib/cobib/-/tags/v2.2.1
[2.2.0]: https://gitlab.com/cobib/cobib/-/tags/v2.2.0
[2.1.0]: https://gitlab.com/cobib/cobib/-/tags/v2.1.0
[2.0.0]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0
[2.0.0b4]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0b4
[2.0.0b3]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0b3
[2.0.0b2]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0b2
[2.0.0b1]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0b1
[2.0.0b0]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0b0
[2.0.0a2]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0a2
[2.0.0a1]: https://gitlab.com/cobib/cobib/-/tags/v2.0.0a1
[1.1.0]: https://gitlab.com/cobib/cobib/-/tags/v1.1.0
[1.0.2]: https://gitlab.com/cobib/cobib/-/tags/v1.0.2
[1.0.1]: https://gitlab.com/cobib/cobib/-/tags/v1.0.1
[1.0.0]: https://gitlab.com/cobib/cobib/-/tags/v1.0.0
[0.2]: https://gitlab.com/cobib/cobib/-/tags/v0.2
[0.1]: https://gitlab.com/cobib/cobib/-/tags/v0.1
